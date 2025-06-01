import glm
import numpy as np
import time
import OpenGL.GL as gl
from shaderC import Shader

def prGreen(msg): print("\033[92m {}\033[00m".format(msg))
def prRed(msg): print("\033[91m {}\033[00m".format(msg))

class Particles:
    def __init__(self, compute_physics_shader: Shader, compute_partition_shader: Shader):
        self.COMPUTE_SHADER = compute_physics_shader
        self.COMPUTE_PARTITION_SHADER = compute_partition_shader
        self.particleCount = 5_000
        self.frameCount = 0
        self.numTypes = 4
        self.gridSize = 100
        self.cellSize = 1.0
        self.deltaTime = 0.001
        self.stepSize = 0.6
        self.randomSeed = 10
        self.maxInteractions = 500
        self.particleRadius = 0.1
        self.detectionRadius = 1.0
        self.tooCloseRadius = 0.5
        self.forceStrengthFactor = 1.0
        self.closeRepellentForce = 1.0
        self.spawnGridSize = 20
        self.runSimulation = True
        self.useManualForceMatrix = False
        self.manualForceMatrix = glm.mat4(1.0)

        self.LOCAL_X_CP = 512
        self.LOCAL_X_CS = 1024
        self.dispatchCount_CS = (self.particleCount + self.LOCAL_X_CS - 1) // self.LOCAL_X_CS
        self.dispatchCount_CP = (self.particleCount + self.LOCAL_X_CP - 1) // self.LOCAL_X_CP
        
        self.floatsPerParticle = 8

        self.update_gridCellCount()
        self.init_particles()
        self.init_particle_ssbo()
        self.init_partition_buffers()
        

    def update_gridCellCount(self):
        self.gridCellCount = self.gridSize ** 3

    def init_particles(self):
        if isinstance(self.gridSize, (list, tuple)):
            gs_vec = glm.vec3(self.gridSize[0], self.gridSize[1], self.gridSize[2])
        else:
            gs_vec = glm.vec3(self.spawnGridSize)
        
        world_half_extents = gs_vec * 0.5

        low_bounds = np.array([-world_half_extents.x, -world_half_extents.y, -world_half_extents.z], dtype=np.float32)
        high_bounds = np.array([world_half_extents.x, world_half_extents.y, world_half_extents.z], dtype=np.float32)
        
        positions = np.random.uniform(low=low_bounds, high=high_bounds, size=(self.particleCount, 3)).astype(np.float32)
        

        velocities = np.zeros((self.particleCount, 3), dtype=np.float32) 
        types = np.random.randint(0, self.numTypes, size=(self.particleCount, 1)).astype(np.float32)
        
        self.particle_data = np.zeros((self.particleCount, self.floatsPerParticle), dtype=np.float32)
        self.particle_data[:, 0:3] = positions             
        self.particle_data[:, 3]   = 0.0                  
        self.particle_data[:, 4:7] = velocities            
        self.particle_data[:, 7]   = types.flatten()        

    def init_particle_ssbo(self):
        self.buffer_size = self.particleCount * self.floatsPerParticle * np.dtype(np.float32).itemsize
        
        if hasattr(self, 'ssbo') and gl.glIsBuffer(self.ssbo):
            gl.glDeleteBuffers(1, [self.ssbo])

        self.ssbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.ssbo)
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, self.buffer_size, self.particle_data, gl.GL_DYNAMIC_DRAW)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, self.ssbo)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, 0)

    def dispatch_particles(self):
        self.dispatchCount_CS = (self.particleCount + 1023) // 1024
        self.dispatchCount_CP = (self.particleCount + self.LOCAL_X_CP - 1) // self.LOCAL_X_CP
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, self.ssbo)
        self.COMPUTE_SHADER.dispatch(self.dispatchCount_CS, 1, 1)

    def init_partition_buffers(self):
        if hasattr(self, 'grid_head_ssbo') and self.grid_head_ssbo != 0 and gl.glIsBuffer(self.grid_head_ssbo):
            gl.glDeleteBuffers(1, [self.grid_head_ssbo])
            self.grid_head_ssbo = 0 
        if hasattr(self, 'particle_links_ssbo') and self.particle_links_ssbo != 0 and gl.glIsBuffer(self.particle_links_ssbo):
            gl.glDeleteBuffers(1, [self.particle_links_ssbo])
            self.particle_links_ssbo = 0 

        self.grid_head_data = np.full(self.gridCellCount, -1, dtype=np.int32)
        self.grid_head_ssbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.grid_head_ssbo)
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, self.grid_head_data.nbytes, self.grid_head_data, gl.GL_DYNAMIC_DRAW)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, self.grid_head_ssbo)

        self.particle_links_data = np.full(self.particleCount, -1, dtype=np.int32)
        self.particle_links_ssbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.particle_links_ssbo)
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, self.particle_links_data.nbytes, self.particle_links_data, gl.GL_DYNAMIC_DRAW)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, self.particle_links_ssbo)

        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, 0) 
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, 0) 
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, 0) 
        gl.glUseProgram(0)

    def reset_partition_buffers(self):
        self.grid_head_data.fill(-1)
        self.particle_links_data.fill(-1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.grid_head_ssbo)
        gl.glBufferSubData(gl.GL_SHADER_STORAGE_BUFFER, 0, self.grid_head_data.nbytes, self.grid_head_data)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.particle_links_ssbo)
        gl.glBufferSubData(gl.GL_SHADER_STORAGE_BUFFER, 0, self.particle_links_data.nbytes, self.particle_links_data)

        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, 0)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, 0)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, 0)
        gl.glUseProgram(0)

    def execute_partitioning(self):
        self.reset_partition_buffers()
        gl.glUseProgram(self.COMPUTE_PARTITION_SHADER.program)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_PARTITION_SHADER.program, "gridSize"), self.gridSize)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_PARTITION_SHADER.program, "cellSize"), self.cellSize)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_PARTITION_SHADER.program, "PARTICLE_COUNT"), self.particleCount)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, self.ssbo)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, self.grid_head_ssbo)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, self.particle_links_ssbo)
        self.COMPUTE_PARTITION_SHADER.dispatch(self.dispatchCount_CP, 1, 1)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, 0)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, 0)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, 0)
        gl.glUseProgram(0)

    def execute_particle_physics(self):
        gl.glUseProgram(self.COMPUTE_SHADER.program)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "gridSize"), self.gridSize)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "cellSize"), self.cellSize)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "deltaTime"), self.deltaTime)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "stepSize"), self.stepSize)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "closeRepellentForce"), self.closeRepellentForce)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "forceStrengthFactor"), self.forceStrengthFactor)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "PARTICLE_RADIUS"), self.particleRadius)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "DETECTION_RADIUS"), self.detectionRadius)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "TOO_CLOSE_RADIUS"), self.tooCloseRadius)
        gl.glUniform1f(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "seed"), self.randomSeed)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "MAX_PARTICLE_INTERACTIONS"), self.maxInteractions)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "PARTICLE_COUNT"), self.particleCount)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "ACTIVE_TYPES"), self.numTypes)
        gl.glUniform1i(gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "useManualForceMatrix"), int(self.useManualForceMatrix))
        gl.glUniformMatrix4fv(
            gl.glGetUniformLocation(self.COMPUTE_SHADER.program, "manualForceMatrix"),
            1, gl.GL_FALSE, glm.value_ptr(self.manualForceMatrix)
        )
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, self.ssbo)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, self.grid_head_ssbo)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, self.particle_links_ssbo)
        self.COMPUTE_SHADER.dispatch(self.dispatchCount_CS, 1, 1)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, 0)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, 0)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, 0)
        gl.glUseProgram(0)
        
    def simulate_particles(self):
        self.frameCount += 1
        if self.runSimulation:
            if self.frameCount % 5 == 0:
                self.reset_partition_buffers()
                self.execute_partitioning()
            if self.frameCount % 3 == 0:
                self.execute_particle_physics()

    def update_grid_size(self):
        self.update_gridCellCount()
        self.init_particles()
        self.init_particle_ssbo()
        self.init_partition_buffers()

    def set_particle_count(self):
        self.dispatchCount_CS = (self.particleCount + self.LOCAL_X_CS - 1) // self.LOCAL_X_CS
        self.dispatchCount_CP = (self.particleCount + self.LOCAL_X_CP - 1) // self.LOCAL_X_CP
        self.init_particles()
        self.init_particle_ssbo()
        self.init_partition_buffers()

