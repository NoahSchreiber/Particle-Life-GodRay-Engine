import OpenGL.GL as gl
import glm
import imgui  
import glfw

from guiC import GUI
from gameC import Game
from cameraC import Camera

def run():
    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
    glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

    engine_window = glfw.create_window(900, 900, "GodRay Engine", None, None)
    
    if not engine_window:
        glfw.terminate()
        return

    glfw.make_context_current(engine_window)
    glfw.set_window_pos(engine_window, 200, 200)
    glfw.set_framebuffer_size_callback(engine_window, framebuffer_size_callback)
    glfw.set_input_mode(engine_window, glfw.CURSOR,  glfw.CURSOR_DISABLED)

    gui = GUI(imgui, engine_window)
    
    global game
    game = Game()
    game.camera.first_mouse = True
    
    framebuffer_size_callback(engine_window, game.RENDER_SETTINGS["Width"], game.RENDER_SETTINGS["Heigt"])
    
    glfw.set_scroll_callback(engine_window, game.camera.scroll_callback)
    glfw.set_cursor_pos_callback(engine_window, lambda win, xpos, ypos: game.camera.process_mouse_movement(xpos, ypos))

    last_fps_time = glfw.get_time()
    frame_count = 0

    while not glfw.window_should_close(engine_window):
        glfw.poll_events()
        gui.imgui_renderer.process_inputs()       
            
        currentFrame = glfw.get_time()
        
        game.camera.frameCount += 1
        game.camera.deltaTime = currentFrame - game.camera.lastFrame
        game.camera.lastFrame = currentFrame
        
        game.particles.deltaTime = game.camera.deltaTime
        game.particles.simulate_particles()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # type: ignore
        
        game.camera.process_input(engine_window)
        
        game.render.scene()
        
        imgui.new_frame() # type: ignore
        gui.render_particle_graphics(game.particles)
        gui.render_particle_settings(game.particles)
        gui.imgui.render() # type: ignore
        gui.imgui_renderer.render(imgui.get_draw_data()) # type: ignore
        
        glfw.swap_buffers(engine_window)
        
        frame_count += 1
        current_time = glfw.get_time()
        if current_time - last_fps_time >= 0.1:
            fps = frame_count / (current_time - last_fps_time)
            glfw.set_window_title(engine_window, f"GodRay Engine - FPS: {fps:.1f}")
            last_fps_time = current_time
            frame_count = 0


        if glfw.get_key(engine_window, glfw.KEY_HOME) == glfw.PRESS:
            glfw.set_window_should_close(engine_window, True)

        if glfw.get_key(engine_window, glfw.KEY_R) == glfw.PRESS and not game.TRIGGER_RELOAD_CONFIG:
            game.TRIGGER_RELOAD_CONFIG = True # type: ignore
            
        if glfw.get_key(engine_window, glfw.KEY_R) == glfw.RELEASE and game.TRIGGER_RELOAD_CONFIG:
            game.reload_shaders()
            game.TRIGGER_RELOAD_CONFIG = False

    gui.imgui_renderer.shutdown()
    glfw.terminate()
    print("Bye!")

def framebuffer_size_callback(window, width, height):
    global game 
    gl.glViewport(0, 0, width, height)
    for name, FBO in game.ALL_OBJECTS_FRAMEBUFFERS.items():
        FBO.resize(width, height)
    game.RENDER_SETTINGS["Width"]  = width
    game.RENDER_SETTINGS["Height"] = height
    
    game.camera.resolution = glm.vec2(width, height)
    game.camera.aspect_ratio = width / max(1.0, height)
    game.camera.projectionMatrix = glm.perspective(glm.radians(game.camera.FOV), game.camera.aspect_ratio, game.camera.near, game.camera.far)
    imgui.get_io().display_size = glm.vec2(width, height) # type: ignore

if __name__ == "__main__":
    run()
