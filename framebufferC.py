
def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))

import glm
import OpenGL.GL as gl
from PIL import Image
import numpy as np
import ctypes


class Framebuffer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.FBO = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.FBO)
        self._create_attachments()
        self.check_complete()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def bind(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.FBO)

    def unbind(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def resize(self, width, height):
        self.width = width
        self.height = height
        self._resize_attachments()

    def check_complete(self):
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            prRed(f"[FBO] Incomplete framebuffer: {type(self).__name__}")

    def _create_attachments(self):
        raise NotImplementedError

    def _resize_attachments(self):
        raise NotImplementedError


    @classmethod
    def load_all_framebuffers(cls, repository_framebuffers):
        loaded = {}
        for name, config in repository_framebuffers.items():
            fb_type = config["type"]
            cfg = config["config"]

            width = cfg.get("width")
            height = cfg.get("height")

            if fb_type == "Display":
                fb = DisplayFramebuffer(width, height)
            elif fb_type == "HDR":
                samples = cfg.get("samples")
                fb = HDRFramebuffer(width, height, samples)
            elif fb_type == "Depth":
                fb = DepthFramebuffer(width, height)
            elif fb_type == "Bloom":
                fb = BloomFramebuffer(width, height)
            elif fb_type == "DownSample":
                fb = DownSampleFramebuffer(width, height)
            else:
                raise ValueError(f"[FBO] Unknown framebuffer type: {fb_type}")
            prGreen(f"[FBO] Loaded '{name}' — : {fb_type}")
            prLightGray("")
            loaded[name] = fb
        return loaded
    
class DisplayFramebuffer(Framebuffer):
    def _create_attachments(self):
        self.displayTexture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.displayTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA16F, self.width, self.height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.displayTexture, 0)

    def _resize_attachments(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.displayTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA16F, self.width, self.height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)


class HDRFramebuffer(Framebuffer):
    def __init__(self, width, height, samples):
        self.samples = samples
        super().__init__(width, height)

    def _create_attachments(self):
        self.colorBuffer = gl.glGenTextures(1)
        self.depthBuffer = gl.glGenRenderbuffers(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D_MULTISAMPLE, self.colorBuffer)
        gl.glTexImage2DMultisample(gl.GL_TEXTURE_2D_MULTISAMPLE, self.samples, gl.GL_RGBA16F, self.width, self.height, gl.GL_TRUE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D_MULTISAMPLE, self.colorBuffer, 0)

        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depthBuffer)
        gl.glRenderbufferStorageMultisample(gl.GL_RENDERBUFFER, self.samples, gl.GL_DEPTH_COMPONENT, self.width, self.height)
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.depthBuffer)

        self.VAO = gl.glGenVertexArrays(1)
        self.index_count = 6
        gl.glBindVertexArray(self.VAO)

        quad_vertices = [
            -1.0,  1.0, 0.0,   0.0, 1.0,
            -1.0, -1.0, 0.0,   0.0, 0.0,
             1.0, -1.0, 0.0,   1.0, 0.0,
            -1.0,  1.0, 0.0,   0.0, 1.0,
             1.0, -1.0, 0.0,   1.0, 0.0,
             1.0,  1.0, 0.0,   1.0, 1.0
        ]
        quad_vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, quad_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, np.array(quad_vertices, dtype=np.float32), gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 5 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 5 * 4, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)

    def _resize_attachments(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D_MULTISAMPLE, self.colorBuffer)
        gl.glTexImage2DMultisample(gl.GL_TEXTURE_2D_MULTISAMPLE, self.samples, gl.GL_RGBA16F, self.width, self.height, gl.GL_TRUE)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depthBuffer)
        gl.glRenderbufferStorageMultisample(gl.GL_RENDERBUFFER, self.samples, gl.GL_DEPTH_COMPONENT, self.width, self.height)


class DepthFramebuffer(Framebuffer):
    def _create_attachments(self):
        self.depthTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.depthTex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT32F, self.width, self.height, 0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, self.depthTex, 0)
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)

    def _resize_attachments(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.depthTex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT32F, self.width, self.height, 0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)


class BloomFramebuffer(Framebuffer):
    def _create_attachments(self):
        self.bloomTexture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bloomTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA16F, self.width, self.height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.bloomTexture, 0)

    def _resize_attachments(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bloomTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA16F, self.width, self.height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)


class DownSampleFramebuffer(Framebuffer):
    def _create_attachments(self):
        self.downsampledTexture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.downsampledTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA16F, self.width, self.height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.downsampledTexture, 0)

    def _resize_attachments(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.downsampledTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA16F, self.width, self.height, 0, gl.GL_RGBA, gl.GL_FLOAT, None)
