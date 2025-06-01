""" CONTAINS
        Model Class and corresponding Subclasses """

import pprint
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))


import glm
import OpenGL.GL as gl
import ctypes
from loadC import Load

class Model:
    def __init__(self, vertices, indices, model_material):
        self.vertices = vertices
        self.indices = indices 
        self.index_count = len(indices)
        
        self.model_material = model_material # Not using this yet! might be good for the future 

        self.VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.VAO)
        
        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        self.EBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

        stride = 14 * ctypes.sizeof(gl.GLfloat)

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)

        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(gl.GLfloat)))
        gl.glEnableVertexAttribArray(1)

        gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(6 * ctypes.sizeof(gl.GLfloat)))
        gl.glEnableVertexAttribArray(2)

        gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(8 * ctypes.sizeof(gl.GLfloat)))
        gl.glEnableVertexAttribArray(3)

        gl.glVertexAttribPointer(4, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(11 * ctypes.sizeof(gl.GLfloat)))
        gl.glEnableVertexAttribArray(4)

        gl.glBindVertexArray(0)
        

    @classmethod
    def load_all_models(cls, REPOSITORY_MODELS):
        loaded = {}
        for fullObjectName, repo in REPOSITORY_MODELS.items():
            path = repo.get("path")
            scale =  repo.get("scale")
            fullObjectData = Load.read_Obj_File(path)
            
            fullObject = []
            
            for key, subObjectData in fullObjectData.items():
                vertices = subObjectData.get('vertices')
                indices  = subObjectData.get("indices")
                material = subObjectData.get('material')[0]

                subModel = Model(vertices, indices, material)
                fullObject.append(subModel)

                prCyan(f"[Model] subObject Loaded: '{key}' — Size: {len(vertices)}, Material: {material}")

            loaded[fullObjectName] = fullObject
            prGreen(f"[Model] Object Loaded: {fullObjectName}")
            prLightGray("")
        return loaded
        
        