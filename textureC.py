import pprint
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))

""" CONTAINS
        Texture Class and corresponding Subclasses """

import OpenGL.GL as gl
from PIL import Image
import os
import sys
import json

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) # type: ignore
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)



class Texture:
    def __init__(self, path, params=None, tex_type="2D"):
        self.file_path = resource_path(path)
        self.params = params or {}
        self.tex_type = tex_type
        self.tid = Texture.add_texture(self.file_path, self.params, self.tex_type)

    
    
    @classmethod
    def load_all_textures(cls, ALL_OBJECTS_TEXTURES):
        loaded = {}
        for name, repo in ALL_OBJECTS_TEXTURES.items():
            path = repo.get("path")
            params = repo.get("params", {})
            tex_type = repo.get("type", "2D")
            loaded[name] = cls(path, params, tex_type)
        return loaded

    
    @staticmethod
    def load_texture_repository(path, ALL_OBJECTS_MATERIALS={}):
        repository_textures = {}
        with open(resource_path(path), "r") as f:
            repo = json.load(f)
        for name, cfg in repo.items():
            repository_textures[name] = {
                "type": cfg.get("type", "2D"),
                "path": cfg["path"],
                "params": cfg.get("params", {})  # filtering, wrapping, etc.
            }

        for fullMaterial in ALL_OBJECTS_MATERIALS.values():
            for subMaterial in fullMaterial:
                for global_texture_name, global_texture_data  in subMaterial.global_textures.items():
                    repository_textures[global_texture_name] = {
                        "type": global_texture_data.get("type", "2D"),
                        "path": global_texture_data["path"],
                        "params": global_texture_data.get("params", {})  # filtering, wrapping, etc.
                    }
                
        print(f"[Texture] Loaded texture configs: {list(repository_textures.keys())}")
        return repository_textures
    

    @staticmethod
    def resolve_texture_type(type_str):
        type_map = {
            "2D": gl.GL_TEXTURE_2D,
            "CUBE": gl.GL_TEXTURE_CUBE_MAP,
            "3D": gl.GL_TEXTURE_3D
        }
        return type_map.get(type_str.upper(), gl.GL_TEXTURE_2D)


    @staticmethod
    def add_texture(file_path, params, tex_type):
        width, height, data = Texture.load_image(file_path)
        tid = gl.glGenTextures(1)

        gl_type = Texture.resolve_texture_type(tex_type)

        gl.glBindTexture(gl_type, tid)

        # Default params
        wrap_s = params.get("wrap_s", gl.GL_REPEAT)
        wrap_t = params.get("wrap_t", gl.GL_REPEAT)
        min_filter = params.get("min_filter", gl.GL_LINEAR_MIPMAP_LINEAR)
        mag_filter = params.get("mag_filter", gl.GL_LINEAR)

        gl.glTexParameteri(gl_type, gl.GL_TEXTURE_WRAP_S, wrap_s)
        gl.glTexParameteri(gl_type, gl.GL_TEXTURE_WRAP_T, wrap_t)
        gl.glTexParameteri(gl_type, gl.GL_TEXTURE_MIN_FILTER, min_filter)
        gl.glTexParameteri(gl_type, gl.GL_TEXTURE_MAG_FILTER, mag_filter)

        if gl_type == gl.GL_TEXTURE_2D:
            gl.glTexImage2D(gl_type, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
            gl.glGenerateMipmap(gl_type)
        else:
            raise NotImplementedError(f"[Texture]  Texture type '{tex_type}' not supported yet.")

        return tid


    
    @staticmethod
    def load_image(file_path):
        try:
            image = Image.open(resource_path(file_path))
            image = image.transpose(Image.FLIP_TOP_BOTTOM) # type: ignore
            image_data = image.convert("RGBA").tobytes()  
            width, height = image.size

            return width, height, image_data
        except:
            print(f"[TEX] PATH NOT FOUND {file_path}")
            return 1, 1, []
    