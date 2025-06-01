from loadC import Load
from modelC import Model
from cameraC import Camera
from renderC import Render
from shaderC import Shader
from textureC import Texture
from materialsC import Material
from particlesC import Particles
from framebufferC import Framebuffer
from world_ObjectC import World_Object

class Game:
    def __init__(self):

        self.RENDER_SETTINGS = {
                                "HDR_ENABLED": False,
                                "Width": 900,
                                "Heigt": 900
                                }

        self.camera = Camera(self.RENDER_SETTINGS["Width"],self.RENDER_SETTINGS["Heigt"], 60)
        
        self.load_config()
         
        self.TRIGGER_RELOAD_CONFIG = False
        self.TRIGGER_RELOAD_SHADER = False
      
    def load_config(self):
        
        self.REPOSITORY_SHADERS      = Load.load_shader_repository("config/repository_shaders.json")
        self.ALL_OBJECTS_SHADERS      = Shader.load_all_shaders(self.REPOSITORY_SHADERS)
        
        
        self.REPOSITORY_FRAMEBUFFERS = Load.load_framebuffer_repository("config/repository_framebuffers.json")
        self.ALL_OBJECTS_FRAMEBUFFERS = Framebuffer.load_all_framebuffers(self.REPOSITORY_FRAMEBUFFERS)
        
        
        self.REPOSITORY_MATERIALS    = Material.load_material_repository("config/repository_materials.json")    
        self.ALL_OBJECTS_MATERIALS    = Material.load_all_materials(self.REPOSITORY_MATERIALS)
        
        
        self.REPOSITORY_TEXTURES     = Texture.load_texture_repository("config/repository_textures.json", self.ALL_OBJECTS_MATERIALS)
        self.ALL_OBJECTS_TEXTURES     = Texture.load_all_textures(self.REPOSITORY_TEXTURES)
        
        self.REPOSITORY_MODELS       = Load.load_model_repository("config/repository_models.json")
        self.ALL_OBJECTS_MODELS       = Model.load_all_models(self.REPOSITORY_MODELS)
        
        
        self.REPOSITORY_SCENE        = Load.load_scene_repository("config/repository_scene.json")
        self.ALL_WORLD_OBJECTS        = World_Object.load_scene(self.REPOSITORY_SCENE, self.ALL_OBJECTS_MODELS, self.ALL_OBJECTS_TEXTURES, self.ALL_OBJECTS_MATERIALS) 
        
        self.particles = Particles(self.ALL_OBJECTS_SHADERS["particles_cs"],
                                   self.ALL_OBJECTS_SHADERS["particles_partition_cs"])
        
        self.render = Render(self.ALL_OBJECTS_SHADERS,  self.ALL_OBJECTS_FRAMEBUFFERS,
                             self.ALL_OBJECTS_TEXTURES, self.ALL_OBJECTS_MATERIALS,
                             self.ALL_OBJECTS_MODELS,   self.ALL_WORLD_OBJECTS,
                             self.RENDER_SETTINGS,      self.camera, self.particles)
            
        self.TRIGGER_RELOAD_CONFIG = False
        print("[GAME] CONFIG LOADED")
        
    def reload_shaders(self):
        
        for _, shader in self.ALL_OBJECTS_SHADERS.items():
            shader.reload()
            
        self.TRIGGER_RELOAD_SHADER = False
