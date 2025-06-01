from imgui.integrations.glfw import GlfwRenderer
import random
import colorsys

class GUI:
    def __init__(self, imgui, engine_window):
        self.imgui = imgui
        self.imgui.create_context()
        self.imgui_renderer = GlfwRenderer(engine_window) 
        self.io = imgui.get_io()

    def render_save_settings(self):
        self.imgui.begin("Settings")
        if self.imgui.button("Save All Repositories"):
            print("[ADD] SAVE FUNCTION")
        self.imgui.end()

    def render_particle_graphics(self, particles):
        self.imgui.begin("Particle Graphics")
        self.imgui.separator()
        self.imgui.text("Size")
        changed, new_pR = self.imgui.slider_float(
            "Particle Radius", particles.particleRadius, 0.001, 0.1, format="%.4f"
        )
        if changed:
            particles.particleRadius = new_pR
            particles.tooCloseRadius = max(particles.tooCloseRadius, particles.particleRadius + 0.01)
        self.imgui.end()
              
    def render_particle_settings(self, particles):
        self.imgui.begin("Particle Settings")
        self.imgui.text("Simulation Parameters")
        changed, new_sz = self.imgui.slider_float("Step Size", particles.stepSize, 0.001, 10.0, format="%.4f")
        if changed:
            particles.stepSize = new_sz
        self.imgui.separator()
        self.imgui.text("Interaction Parameters")
        changed, new_mI = self.imgui.slider_int("Max Interactions", particles.maxInteractions, 10, 5_000)
        if changed:
            particles.maxInteractions = new_mI
        changed, new_d = self.imgui.slider_float("Detection Radius", particles.detectionRadius, 0.01, 3.0, format="%.3f")
        if changed:
            particles.detectionRadius = new_d
        changed, new_c = self.imgui.slider_float("Too Close Radius", particles.tooCloseRadius, max(0.01, particles.particleRadius), 3.0, format="%.3f")
        if changed:
            particles.tooCloseRadius = new_c
            particles.tooCloseRadius = max(particles.tooCloseRadius, particles.particleRadius + 0.01)
        self.imgui.text("Start Parameters")
        changed, new_numT = self.imgui.slider_int("Num Types", particles.numTypes, 1, 30)
        if changed:
            particles.numTypes = new_numT
            if particles.useManualForceMatrix:
                particles.numTypes = 4
        changed, new_seed = self.imgui.input_int("Random Matrix", particles.randomSeed)
        if changed:
            particles.randomSeed = new_seed
        changed, run_fMm = self.imgui.checkbox("Manual Force Matrix", particles.useManualForceMatrix)
        if changed:
            particles.useManualForceMatrix = run_fMm
            particles.numTypes = 4
        if particles.useManualForceMatrix:
            self.imgui.text("Manual Force Matrix")
            for i in range(4):
                if i == 0:
                    self.imgui.columns(4, "force_matrix_headers")
                    for col in range(4):
                        self.imgui.set_column_width(col, 90)
                        self.imgui.text(f"Type {col}") 
                        self.imgui.next_column()
                    self.imgui.columns(1)
                else:
                    self.imgui.text(f"Type {i}")
                for j in range(4):
                    val = particles.manualForceMatrix[i][j]
                    norm_val = max(-1.0, min(1.0, val))
                    brightness = abs(norm_val)
                    if norm_val > 0:
                        hue = 0.25 
                    elif norm_val < 0:
                        hue = 0.7  
                    else:
                        hue = 0.0 
                    bright = 0.5 
                    if i == j:
                        base_color = (0.2 * bright, 0.7 * bright, 0.2 * bright, 1.0)
                    elif abs(i - j) == 1:
                        base_color = (0.95 * bright, 0.9 * bright, 0.1 * bright, 1.0)
                    elif abs(i - j) == 2:
                        base_color = (1.0 * bright, 0.55 * bright, 0.15 * bright, 1.0)
                    elif abs(i - j) == 3:
                        base_color = (0.9 * bright, 0.1 * bright, 0.15 * bright, 1.0)
                    else:
                        base_color = (1.0 * bright, 1.0 * bright, 1.0 * bright, 1.0)
                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0 if brightness > 0 else 0.0, brightness)
                    color = (r, g, b, 1.0)
                    self.imgui.push_style_color(self.imgui.COLOR_SLIDER_GRAB, *base_color)
                    self.imgui.push_style_color(self.imgui.COLOR_SLIDER_GRAB_ACTIVE, *base_color)
                    self.imgui.push_style_color(self.imgui.COLOR_FRAME_BACKGROUND, *color)
                    self.imgui.set_next_item_width(80)
                    label = f"##m[{i}][{j}]"
                    changed, val = self.imgui.slider_float(label, val, -1.0, 1.0, format="%.2f")
                    self.imgui.pop_style_color(3)
                    if changed:
                        particles.manualForceMatrix[i][j] = val
                    if j < 3:
                        self.imgui.same_line()
            if self.imgui.button("Reset Matrix"):
                for i in range(4):
                    for j in range(4):
                        particles.manualForceMatrix[i][j] = 0.0
            self.imgui.same_line()
            if self.imgui.button("Randomize Matrix"):
                for i in range(4):
                    for j in range(4):
                        particles.manualForceMatrix[i][j] = random.uniform(-1.0, 1.0)
        changed, new_mp = self.imgui.slider_int("Particle Count", particles.particleCount, 10, 30_000)
        if changed:
            particles.particleCount = new_mp
            particles.set_particle_count()
        changed, new_ns = self.imgui.slider_int("Spawn Size", particles.spawnGridSize, 10, 50)
        if changed:
            particles.spawnGridSize = new_ns
            particles.cellSize = particles.detectionRadius + 0.1
            particles.set_particle_count()
            particles.update_grid_size()
        self.imgui.separator()
        if self.imgui.button("Reinitialize Particles"):
            particles.cellSize = particles.detectionRadius + 0.1
            particles.init_particles()
            particles.init_particle_ssbo()
        changed, run_sim = self.imgui.checkbox("Run Simulation", particles.runSimulation)
        if changed:
            particles.runSimulation = run_sim
        self.imgui.end()
