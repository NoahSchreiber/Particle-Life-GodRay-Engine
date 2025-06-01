""" CONTAINS
        Shader Class and corresponding Subclasses """

def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))

import OpenGL.GL  as gl
from textureC import Texture

import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) # type: ignore
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class Shader:
    def __init__(self, vertex_directory=None, fragment_directory=None, compute_directory=None, shader_uniforms=None):
        print("[Shader] Initializing shader...")
        self.vertex_path = vertex_directory
        self.fragment_path = fragment_directory
        self.compute_path = compute_directory
        self.program = None
        self.uniforms = shader_uniforms or {}
        self.organize_uniforms()
        self.reload()

    def organize_uniforms(self):
        print("[Shader] Organizing uniforms...")
        self.uniforms_float = {}
        self.uniforms_int = {}
        self.uniforms_vec2 = {}
        self.uniforms_vec3 = {}

        for name, data in self.uniforms.items():
            if isinstance(data, (tuple, list)) and len(data) == 3:
                type_, value, _ = data
            else:
                type_, value = data

            if type_ == "float":
                self.uniforms_float[name] = value
            elif type_ == "int":
                self.uniforms_int[name] = value
            elif type_ == "vec2":
                self.uniforms_vec2[name] = value
            elif type_ == "vec3":
                self.uniforms_vec3[name] = value
        print(f"[Shader] Uniform organization complete: {len(self.uniforms)} uniforms found.")

    def update_uniform(self, uniform_name, value):
        if uniform_name in self.uniforms:
            data = self.uniforms[uniform_name]
            if isinstance(data, (tuple, list)) and len(data) == 3:
                uniform_type, _, widget_type = data
                self.uniforms[uniform_name] = (uniform_type, value, widget_type)
            else:
                uniform_type, _ = data
                self.uniforms[uniform_name] = (uniform_type, value)

            # update typed maps
            if uniform_type == "float":    self.uniforms_float[uniform_name] = value
            elif uniform_type == "int":    self.uniforms_int[uniform_name] = value
            elif uniform_type == "vec2":   self.uniforms_vec2[uniform_name] = value
            elif uniform_type == "vec3":   self.uniforms_vec3[uniform_name] = value

    def use(self):
        """
        Activate this shader program and send all uniforms to GPU.
        """
        if self.program:
            gl.glUseProgram(self.program)
            self.send_uniforms()
        else:
            raise RuntimeError("Shader program is not valid.")

    def send_uniforms(self):
        """ Upload stored uniform values for this program. """
        for name, value in self.uniforms_float.items():
            loc = gl.glGetUniformLocation(self.program, name)
            if loc != -1: gl.glUniform1f(loc, value)
        for name, value in self.uniforms_int.items():
            loc = gl.glGetUniformLocation(self.program, name)
            if loc != -1: gl.glUniform1i(loc, value)
        for name, value in self.uniforms_vec2.items():
            loc = gl.glGetUniformLocation(self.program, name)
            if loc != -1: gl.glUniform2fv(loc, 1, value)
        for name, value in self.uniforms_vec3.items():
            loc = gl.glGetUniformLocation(self.program, name)
            if loc != -1: gl.glUniform3fv(loc, 1, value)

    def dispatch(self, x, y=1, z=1):
        if not self.program or not self.compute_path:
            raise RuntimeError("No compute shader loaded")
        gl.glUseProgram(self.program)
        self.send_uniforms()
        gl.glDispatchCompute(x, y, z)
        gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT | gl.GL_TEXTURE_FETCH_BARRIER_BIT) # type: ignore

    def reload(self):
        try:
            if self.compute_path is not None:
                print(f"[Shader] Reloading compute shader: {self.compute_path}")
                source = self.load_source(self.compute_path)
                self.compute_source = source
                self.program = self.create_compute_program(source)
                prGreen("[Shader] Compute shader reload successful.")
                prLightGray("")
            elif self.vertex_path is not None and self.fragment_path is not None:
                print(f"[Shader] Reloading vertex/fragment: {self.vertex_path}, {self.fragment_path}")
                vs = self.load_source(self.vertex_path)
                fs = self.load_source(self.fragment_path)
                self.vertex_source = vs
                self.fragment_source = fs
                self.program = self.create_shader_program(vs, fs)
                prGreen("[Shader] V/Fragment reload successful.")
                prLightGray("")
            else:
                prRed("[Shader] [Warning!] No Path could be found.")         

            # Immediately use and upload uniforms on load
            gl.glUseProgram(self.program)
            self.send_uniforms()

        except Exception as e:
            print(f"[Shader] Reload failed: {e}")
            self.program = None

    @staticmethod
    def load_source(path):
        print(f"[Shader] Loading source: {path}")
        with open(resource_path(path)) as f:
            return f.read()

    @staticmethod
    def compile_shader(shaderType, source):
        shader = gl.glCreateShader(shaderType)
        gl.glShaderSource(shader, source)
        gl.glCompileShader(shader)
        if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
            log = gl.glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"Shader compile error: {log}")
        return shader

    @classmethod
    def create_shader_program(cls, vs_source, fs_source):
        vs = cls.compile_shader(gl.GL_VERTEX_SHADER, vs_source)
        fs = cls.compile_shader(gl.GL_FRAGMENT_SHADER, fs_source)
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs); gl.glAttachShader(prog, fs)
        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            log = gl.glGetProgramInfoLog(prog).decode()
            raise RuntimeError(f"Program link error: {log}")
        gl.glDeleteShader(vs); gl.glDeleteShader(fs)
        return prog

    @classmethod
    def create_compute_program(cls, source):
        cs = cls.compile_shader(gl.GL_COMPUTE_SHADER, source)
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, cs)
        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            log = gl.glGetProgramInfoLog(prog).decode()
            raise RuntimeError(f"Compute link error: {log}")
        gl.glDeleteShader(cs)
        return prog
    
    @classmethod
    def load_all_shaders(cls, repository_shaders):
        loaded = {}
        for name, repo in repository_shaders.items():
            shader_type = repo.get("type", "graphics")
            uniforms = repo.get("uniforms", {})

            if shader_type == "compute":
                compute = repo.get("path")
                if not compute:
                    prRed("[Shader] [Warning!] Skipping '{name}' — no compute path provided.")
                    continue
                vertex = fragment = None
            else:  # "graphics"
                vertex = repo.get("vertex")
                fragment = repo.get("fragment")
                compute = None
                if not vertex or not fragment:
                    prRed("[Shader] [Warning!] '{name}' — missing vertex or fragment shader.")
                    continue

            print(f"[Shader] Loading '{name}' — V: {vertex}, F: {fragment}, C: {compute}")
            loaded[name] = cls(vertex, fragment, compute, uniforms)
        return loaded

            


