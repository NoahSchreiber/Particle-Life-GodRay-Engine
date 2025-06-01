""" World_Object Class contains an Object that has a
    Position
    Rotation
    and one or more Models which are bound to each other
    The individual Models can contain different Materials / Textures"""
import glm
import pprint
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))
def prRed(skk): print("\033[91m {}\033[00m".format(skk))




class World_Object:
    def __init__(self, model_name, material_name, position, rotation, scale):
        self.model_name = model_name
        self.material_name = material_name
        self.position        = position
        self.rotation   = rotation
        self.scale      = scale
        


    @classmethod
    def load_scene(cls, REPOSITORY_SCENE, ALL_OBJECTS_MODELS, ALL_OBJECTS_TEXTURES, ALL_OBJECTS_MATERIALS) :
        loaded = []
        
        for ObjectName, parameters in REPOSITORY_SCENE.items():
            
            
            model_name = parameters["model_name"]
            material_name = parameters["material_name"]
            
            
            if ALL_OBJECTS_MODELS.get(model_name, None) is None:
                prRed(f"[World_Object] [WARNING] Tried Loading: '{ObjectName}' model_name: {model_name} NOT FOUND")
                
            
            elif ALL_OBJECTS_MATERIALS.get(material_name, None) is None:
                prRed(f"[World_Object] [WARNING] Tried Loading: '{ObjectName}' material_name: {material_name} NOT FOUND")
                
            else:
                position   = parameters["position"]
                rotation   = parameters["rotation"]
                scale      = parameters["scale"]
                
                
                worldObject = World_Object(model_name, material_name, position, rotation, scale)
                loaded.append(worldObject)
                prCyan(f"[World_Object] Loaded: '{ObjectName}' Mtl: {material_name},\nPos: {position},\nRot: {rotation},\nScale: {scale}")
                
                
        prLightGray("")
        return loaded
        
        