""" CONTAINS
        Load Class and corresponding Subclasses """

import glm
import numpy as np
import json

from framebufferC import HDRFramebuffer, BloomFramebuffer

import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) # type: ignore
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def safe_normalize(v):
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    norms[norms < 1e-6] = 1  # avoid division by zero
    return v / norms

class Load:      
    @staticmethod
    def load_shader_repository(path):
        repository_shaders = {}
        with open(resource_path(path), "r") as f:
            repo = json.load(f)
        for name, cfg in repo.items():
            if "compute" in cfg:
                repository_shaders[name] = {
                    "type": "compute",
                    "path": cfg["compute"],
                    "uniforms": cfg.get("uniforms", {})
                }
            else:
                repository_shaders[name] = {
                    "type": "graphics",
                    "vertex": cfg["vertex"],
                    "fragment": cfg["fragment"],
                    "uniforms": cfg.get("uniforms", {})
                }
        print(f"[Load] Loaded shaders: {list(repository_shaders.keys())}")
        return repository_shaders

    
    @staticmethod
    def load_framebuffer_repository(path):
        repository_framebuffers = {}
        with open(resource_path(path), "r") as f:
            repo = json.load(f)
        for name, cfg in repo.items():
            fb_type = cfg["type"]
            repository_framebuffers[name] = {
                "type": fb_type,
                "config": cfg
            }
        print(f"[Load] Loaded framebuffer configs: {list(repository_framebuffers.keys())}")
        return repository_framebuffers





    @staticmethod
    def load_model_repository(path):
        repository_models = {}
        with open(resource_path(path), "r") as f:
            repo = json.load(f)
        for name, cfg in repo.items():
            repository_models[name] = {
                "path": cfg["path"],
                "material": cfg.get("material", None),
                "instance_count": cfg.get("instance_count", 1)
            }
        print(f"[Load] Loaded model configs: {list(repository_models.keys())}")
        return repository_models
    
    @staticmethod
    def load_scene_repository(path):
        repository_scene = {}
        with open(resource_path(path), "r") as f:
            repo = json.load(f)
        for name, cfg in repo.items():
            repository_scene[name] = {
                "model_name": cfg["model_name"],
                "material_name": cfg["material_name"],
                "position": glm.vec3(*cfg.get("position", [0.0, 0.0, 0.0])),
                "rotation": glm.vec3(*cfg.get("rotation", [0.0, 0.0, 0.0])),
                "scale": cfg.get("scale", 1.0),
            }
        print(f"[Load] Loaded scene configs: {list(repository_scene.keys())}")
        return repository_scene


    @staticmethod
    def transform_obj_data(vertices, normals, textures, faces, material):
        vertices = np.array(vertices, dtype=np.float32)
        normals = np.array(normals, dtype=np.float32)
        textures = np.array(textures, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32).flatten()

        if len(faces) % 9 != 0:
            print("[Load] [WARN] Skipping model with malformed face count.")
            return np.array([], dtype=np.float32), np.array([], dtype=np.int32), material

        v_indices = faces[0::3] - 1
        t_indices = faces[1::3] - 1
        n_indices = faces[2::3] - 1

        indexed_vertices = vertices[v_indices]
        indexed_normals = normals[n_indices]
        indexed_textures = textures[t_indices]

        tangents = np.zeros_like(indexed_vertices)
        bitangents = np.zeros_like(indexed_vertices)

        for i in range(0, len(indexed_vertices), 3):
            try:
                v0, v1, v2 = indexed_vertices[i:i+3]
                uv0, uv1, uv2 = indexed_textures[i:i+3]

                delta_pos1 = v1 - v0
                delta_pos2 = v2 - v0
                delta_uv1 = uv1 - uv0
                delta_uv2 = uv2 - uv0

                denom = (delta_uv1[0] * delta_uv2[1] - delta_uv1[1] * delta_uv2[0])
                if abs(denom) < 1e-8:
                    continue  # skip degenerate triangle
                r = 1.0 / denom

                tangent = (delta_pos1 * delta_uv2[1] - delta_pos2 * delta_uv1[1]) * r
                bitangent = (delta_pos2 * delta_uv1[0] - delta_pos1 * delta_uv2[0]) * r

                tangents[i:i+3] = tangent
                bitangents[i:i+3] = bitangent
            except Exception as e:
                print(f"[WARN] Skipping triangle {i//3}: {e}")
                continue


        tangents = safe_normalize(tangents)
        bitangents = safe_normalize(bitangents)
        
        interleaved = np.hstack((
            indexed_vertices,
            indexed_normals,
            indexed_textures,
            tangents,
            bitangents
        )).astype(np.float32)

        indices = np.arange(len(interleaved), dtype=np.uint32)

        return interleaved, indices, material



    @staticmethod
    def read_Obj_File(filename):
        subobjects = {}
        vertices   = []
        normals    = []
        textures   = []
        faces      = []
        material   = []
        
        current_object_name = "default"
        
        # open the .obj file
        with open(resource_path(filename)) as f:
            lines = f.readlines()

        for line in lines:
            # split the line based on empty space (v 1 2 3) -> (v, 1, 2, 3)
            parts = line.split() 
            if not parts:
                # skip empty lines
                continue  
            
            #skips the prefix
            data = parts[1:] 
            if parts[0] == "o":
                # If this isn't the first object, store the previous one
                if faces:
                    subO_vertices, subO_indices, subO_material = Load.transform_obj_data(vertices, normals, textures, faces, material)
                    subobjects[current_object_name] = {
                        "vertices": subO_vertices,
                        "indices": subO_indices,
                        "material": subO_material
                    }
                    faces, material = [], []
                current_object_name = parts[1]
                
            #specifying the data speeds it up
            elif parts[0] == "vn":
                normals.append([float(normal) for normal in data])
            elif parts[0] == "f":
                faces.append([int(index) for face in data for index in face.split("/")])
            elif parts[0] == "v":
                vertices.append([float(vertex) for vertex in data])
            elif parts[0] == "vt":
                textures.append([float(texture) for texture in data])
            elif parts[0] == "usemtl":
                #usemtl is a string so we can use the entire element
                material.append(data[0]) 
        
        # Save the last object (or the only one)
        if faces:
            subO_vertices, subO_indices, subO_material = Load.transform_obj_data(vertices, normals, textures, faces, material)
            subobjects[current_object_name] = {
                "vertices": subO_vertices,
                "indices": subO_indices,
                "material": subO_material
            }

        return subobjects
                



    @staticmethod
    def read_path_file(file_name):
        vertices = []

        with open(file_name, "r") as f:
            lines = f.readlines()

        for line in lines:
            parts = line.split() 
            if not parts:
                continue  

            if parts[0] == "v":
                vertices.append([float(vertex) for vertex in parts[1:]])
        
        vertices = np.array(vertices, dtype=np.float32)
        
        return vertices
