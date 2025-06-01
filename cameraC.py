import glm
import glfw


class Camera:
    def __init__(self, width, height, FOV):
        self.cameraPos = glm.vec3(1.0, 2.0, 1.0)
        self.cameraFront = glm.vec3(0.0, 0.0, -1.0)
        self.cameraUp = glm.vec3(0.0, 1.0, 0.0)
        self.speed = 2.0
        self.aspect_ratio = width / height
        self.resolution = glm.vec2(width, height)
    
        self.FOV = FOV
        self.far = 5000. 
        self.near = 0.1
        self.view = glm.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)
        self.projectionMatrix = glm.perspective(glm.radians(self.FOV), self.aspect_ratio, self.near, self.far)

        self.lastFrame = 0
        self.deltaTime = 0
        self.frameCount = 0

        self.mouse_captured = True
        self.tab_was_pressed = False

        
        self.yaw = -90.0
        self.pitch = 0.0
        self.lastX = width / 2
        self.lastY = height / 2
        self.first_mouse = True
        self.sensitivity = 0.1

    def update_view(self):
        self.view = glm.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)

    def process_input(self, window) -> None:
        camera_speed = self.speed * self.deltaTime
        
        tab_pressed = glfw.get_key(window, glfw.KEY_TAB) == glfw.PRESS
        if tab_pressed and not self.tab_was_pressed:
            if self.mouse_captured:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                self.mouse_captured = False
            else:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                self.first_mouse = True  
                self.mouse_captured = True
        self.tab_was_pressed = tab_pressed

        if not self.mouse_captured:
            return
        
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            self.cameraPos += camera_speed * self.cameraFront
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            self.cameraPos -= camera_speed * self.cameraFront
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            right = glm.normalize(glm.cross(self.cameraFront, self.cameraUp))
            self.cameraPos -= right * camera_speed
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            right = glm.normalize(glm.cross(self.cameraFront, self.cameraUp))
            self.cameraPos += right * camera_speed
        if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
            self.cameraPos += camera_speed * self.cameraUp
        if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
            self.cameraPos -= camera_speed * self.cameraUp

        self.update_view()


    def process_mouse_movement(self, xpos, ypos):
        if not self.mouse_captured:
            return
        if self.first_mouse:
            self.lastX = xpos
            self.lastY = ypos
            self.first_mouse = False

        xoffset = xpos - self.lastX
        yoffset = self.lastY - ypos  
        self.lastX = xpos
        self.lastY = ypos

        xoffset *= self.sensitivity
        yoffset *= self.sensitivity

        self.yaw += xoffset
        self.pitch += yoffset


        self.pitch = max(-89.0, min(89.0, self.pitch))


        direction = glm.vec3()
        direction.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        direction.y = glm.sin(glm.radians(self.pitch))
        direction.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.cameraFront = glm.normalize(direction)

        self.update_view()
    
    
    def process_scroll(self, yoffset):
        self.speed += self.speed * 0.1 * yoffset
        self.speed = max(self.speed, 0.1)


    def scroll_callback(self, window, xoffset, yoffset):
        if self.mouse_captured:
            self.process_scroll(yoffset)
        
        
    def reset(self):
        self.cameraPos = glm.vec3(1.0, 2.0, 1.0)
        self.cameraFront = glm.vec3(0.0, 0.0, -1.0)
        self.cameraUp = glm.vec3(0.0, 1.0, 0.0)
        self.speed = 50.0

        self.view = glm.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)

        self.currentFrame = 0
        self.deltaTime = 0

        self.mouse_captured = True
        self.tab_was_pressed = False

        
        self.yaw = -90.0
        self.pitch = 0.0
        self.first_mouse = True
        self.sensitivity = 0.1



