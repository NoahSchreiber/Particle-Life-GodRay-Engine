""" CONTAINS
        Material Class and corresponding Subclasses """

def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))

from textureC import Texture
import numpy as np
import json
import glm
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) # type: ignore
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)



class Material:
    def __init__(self, material):
        self.Ka = glm.vec3(1.0, 1.0, 1.0)
        self.Kd = glm.vec3(1.0, 1.0, 1.0)
        self.Ks = glm.vec3(0.5, 0.5, 0.5)
        self.Ke = glm.vec3(0.0, 0.0, 0.0)
        self.Ns = 64.0
        self.Ni = 1.0

        for propertyName, propertyValue in material.items():
            setattr(self, propertyName, propertyValue)
            

            
        self.textures, self.global_textures = self.load_material_textures()


    def load_material_textures(self):
        global_textures = {}
        material_textures = {}
        for key, value in self.__dict__.items():  
            if isinstance(value, str) and value.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tga", ".dds")):
                material_textures[key] = value
                global_textures[value] = {"path": value,
                                          "params": {"wrap": "REPEAT",
                                                    "filter": "LINEAR"}}
        return material_textures, global_textures

        
    @staticmethod
    def read_Mtl_File(filename):
        materials = {}
        currentMaterial = None
        with open(resource_path(filename)) as f:
            for line in f:
                if line.startswith("newmtl"):
                    currentMaterial = line.split()[1]             
                    materials[currentMaterial] = {}
                    materials[currentMaterial]["material_name"] = line.split()[1]
                    print(f"[MTL] Found new material: '{currentMaterial}' in '{filename}'")

               
                if currentMaterial is not None: 
                    if line.startswith("Ka"):  
                        line = line.replace("Ka", "")
                        Ka = ([float(Ka) for Ka in line.split()[:3]])
                        materials[currentMaterial]["Ka"] = glm.vec3(np.array(Ka, dtype=np.float32))
                    
                    elif line.startswith("Kd"): 
                        line = line.replace("Kd", "")
                        Kd = ([float(Kd) for Kd in line.split()[:3]])
                        materials[currentMaterial]["Kd"] = glm.vec3(np.array(Kd, dtype=np.float32))
                    
                    elif line.startswith("Ks"): 
                        line = line.replace("Ks", "")
                        Ks = ([float(Ks) for Ks in line.split()[:3]])
                        materials[currentMaterial]["Ks"] = glm.vec3(np.array(Ks, dtype=np.float32))
                    
                    elif line.startswith("Ns"): 
                        line = line.replace("Ns", "")
                        Ns = float(line[1:])
                        materials[currentMaterial]["Ns"] = np.array(Ns, dtype=np.float32)
                    
                    elif line.startswith("Ke"): 
                        line = line.replace("Ke", "")
                        Ke = ([float(Ke) for Ke in line.split()[:3]])
                        materials[currentMaterial]["Ke"] = glm.vec3(np.array(Ke, dtype=np.float32))
                    
                    elif line.startswith("map_Kd"): 
                        materials[currentMaterial]["map_Kd"] = line[7:].replace("\n", "")
                        
                    elif line.startswith("map_Kn"):
                        materials[currentMaterial]["map_Kn"] = line[7:].replace("\n", "")
                        
                    elif line.startswith("map_Ks"): 
                        materials[currentMaterial]["map_Ks"] = line[7:].replace("\n", "")
                        
                    elif line.startswith("disp"): 
                        materials[currentMaterial]["map_disp"] = line[5:].replace("\n", "")
        print(f"[MTL] Parsed {len(materials)} materials from '{filename}': {list(materials.keys())}")        
        return materials
    
    @classmethod
    def load_all_materials(cls, repository_materials):
        loaded = {}
        for name in repository_materials:
            
            path = repository_materials[name]["path"]
            materials_from_file = Material.read_Mtl_File(path)
            fullMaterial = []
            for material_name, material_data in materials_from_file.items():
                
                fullMaterial.append(Material(material_data))
                
            loaded[name] = fullMaterial
            
        return loaded

            
    @staticmethod
    def load_material_repository(path):
        repository_materials = {}
        with open(resource_path(path), "r") as f:
            repo = json.load(f)
        for name, cfg in repo.items():
            repository_materials[name] = {
                "path": cfg["path"],
            }
        print(f"[MTL] Loaded material configs: {list(repository_materials.keys())}")
        return repository_materials

