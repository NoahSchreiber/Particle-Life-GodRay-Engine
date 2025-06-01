from pprint import pprint
import OpenGL.GL as gl
import glm
from particlesC import Particles

class Render:
    def __init__(self, SHADERS, FRAMEBUFFERS, TEXTURES, MATERIALS, MODELS, WORLD_OBJECTS, SETTINGS, camera, particles: Particles):
        self.SHADERS = SHADERS
        self.FRAMEBUFFERS = FRAMEBUFFERS
        self.TEXTURES = TEXTURES
        self.MATERIALS = MATERIALS
        self.MODELS = MODELS
        self.WORLD_OBJECTS = WORLD_OBJECTS
        self.SETTINGS = SETTINGS
        self.PARTICLES = particles
        self.camera = camera
        
        self.dummy_vao = gl.glGenVertexArrays(1)

        self.RENDER_PASS_DEFS = {
            "display": {
                "SETTINGS": {"SEND_VPM": False, "SCREEN_VAO": True, "CLEAR_COLOR_BUFFER": False},
                "SCREEN_VAO": self.FRAMEBUFFERS["hdr"].VAO,
                "FBO": lambda ctx: 0,
                "SHADER": lambda ctx: ctx.SHADERS["display"],
                "TEX": [
                    {
                        "unit": 1,
                        "target": gl.GL_TEXTURE_2D,
                        "source": lambda ctx: ctx.FRAMEBUFFERS["downsample"].downsampledTexture,
                        "uniform": "downsampledTexture"
                    }
                ],
                "DRAW": lambda ctx, model: gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
            },
            "draw_particles": {
                "SETTINGS": {"SEND_VPM": False, "SCREEN_VAO": False, "CLEAR_COLOR_BUFFER": False},
                "FBO": lambda ctx: ctx.FRAMEBUFFERS["hdr"].FBO,
                "SHADER": lambda ctx: ctx.SHADERS["draw_particles"],
                "TEX": [],
                "DRAW": lambda ctx: (
                    gl.glBindVertexArray(ctx.dummy_vao),
                    gl.glUniform1f(gl.glGetUniformLocation(ctx.SHADERS["draw_particles"].program, "PARTICLE_RADIUS"), self.PARTICLES.particleRadius),
                    gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, ctx.PARTICLES.ssbo),
                    gl.glEnable(gl.GL_PROGRAM_POINT_SIZE),
                    gl.glDrawArrays(gl.GL_POINTS, 0, ctx.PARTICLES.particleCount),
                    gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, 0),
                    gl.glDisable(gl.GL_PROGRAM_POINT_SIZE),
                )
            },
            "draw_grid": {
                "SETTINGS": {"SEND_VPM": True, "SCREEN_VAO": False, "CLEAR_COLOR_BUFFER": True},
                "FBO": lambda ctx: ctx.FRAMEBUFFERS["hdr"].FBO,
                "SHADER": lambda ctx: ctx.SHADERS["draw_grid"],
                "TEX": [],
                "DRAW": lambda ctx: (
                    gl.glBindVertexArray(ctx.dummy_vao),
                    gl.glEnable(gl.GL_BLEND),
                    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA),
                    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6),
                    gl.glDisable(gl.GL_BLEND)
                )
            }
        }

    def scene(self):

        self.run_pass("draw_grid")
            
        self.run_pass("draw_particles")
        self.resolve_hdr_to_display()
        self.run_pass("display")

    def set_common_uniforms(self, shader):
        gl.glUniform3fv(gl.glGetUniformLocation(shader.program, "viewPos"), 1, glm.value_ptr(self.camera.cameraPos))
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(shader.program, "view"), 1, gl.GL_FALSE, glm.value_ptr(self.camera.view))
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(shader.program, "projection"), 1, gl.GL_FALSE, glm.value_ptr(self.camera.projectionMatrix))
        gl.glUniform3fv(gl.glGetUniformLocation(shader.program, "lightPos"), 1, glm.value_ptr(glm.vec3(10., 10., 10)))
        width, height = self.FRAMEBUFFERS["hdr"].width, self.FRAMEBUFFERS["hdr"].height
        loc = gl.glGetUniformLocation(shader.program, "uViewport")
        if loc != -1:
            gl.glUniform2f(loc, width, height)
        gl.glUniform1i(gl.glGetUniformLocation(shader.program, "ACTIVE_TYPES"), self.PARTICLES.numTypes)
        gl.glUniform1i(gl.glGetUniformLocation(shader.program, "PARTICLE_COUNT"), self.PARTICLES.particleCount)

    def bind_material_uniforms(self, shader, material, indx):
        gl.glUniform3fv(gl.glGetUniformLocation(shader.program, "material.Kambient"), 1, glm.value_ptr(material[indx].Ka))
        gl.glUniform3fv(gl.glGetUniformLocation(shader.program, "material.Kdiffuse"), 1, glm.value_ptr(material[indx].Kd))
        gl.glUniform3fv(gl.glGetUniformLocation(shader.program, "material.Kspecular"), 1, glm.value_ptr(material[indx].Ks))
        gl.glUniform3fv(gl.glGetUniformLocation(shader.program, "material.Kemissive"), 1, glm.value_ptr(material[indx].Ke))

    def bind_material_textures(self, shader, material, indx):
        unit = 0
        for texture_type, texture_name in material[indx].textures.items():
            textureObject = self.TEXTURES[texture_name]
            gl.glActiveTexture(gl.GL_TEXTURE0 + unit) # type: ignore
            gl.glBindTexture(gl.GL_TEXTURE_2D, textureObject.tid)
            gl.glUniform1i(gl.glGetUniformLocation(shader.program, texture_name), unit)
            unit += 1

    def run_pass(self, name):
        if name not in self.RENDER_PASS_DEFS:
            print(f"[Render] Unknown pass: {name}")
            return

        STRUCTURE = self.RENDER_PASS_DEFS[name]
        FBO = STRUCTURE["FBO"](self)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, FBO)
        if STRUCTURE["SETTINGS"]["CLEAR_COLOR_BUFFER"]:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # type: ignore
        gl.glDepthMask(gl.GL_TRUE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        shader = STRUCTURE["SHADER"](self)
        if shader.program is None:
            return
        gl.glUseProgram(shader.program)

        self.set_common_uniforms(shader)

        if STRUCTURE["SETTINGS"]["SCREEN_VAO"]:
            gl.glBindVertexArray(STRUCTURE["SCREEN_VAO"])
            for tex in STRUCTURE.get("TEX", []):
                gl.glActiveTexture(gl.GL_TEXTURE0 + tex["unit"])
                gl.glBindTexture(tex["target"], tex["source"](self))
                loc = gl.glGetUniformLocation(shader.program, tex["uniform"])
                gl.glUniform1i(loc, tex["unit"])
            STRUCTURE["DRAW"](self, FBO)
            gl.glBindVertexArray(0)
        else:
            STRUCTURE["DRAW"](self)
            gl.glBindVertexArray(0)

        gl.glUseProgram(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def resolve_hdr_to_display(self):
        HDR_FB = self.FRAMEBUFFERS["hdr"]
        DISPLAY_FB = self.FRAMEBUFFERS["downsample"]
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, HDR_FB.FBO)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, DISPLAY_FB.FBO)
        gl.glBlitFramebuffer(
            0, 0, HDR_FB.width, HDR_FB.height,
            0, 0, DISPLAY_FB.width, DISPLAY_FB.height,
            gl.GL_COLOR_BUFFER_BIT,
            gl.GL_NEAREST
        )
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
