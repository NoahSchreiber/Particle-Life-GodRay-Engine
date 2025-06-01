#version 450

struct Particle {
    vec4 position_stress;
    vec4 velocity_type;
};

layout(std430, binding = 0) buffer ParticleBuffer { Particle particles[]; };

uniform mat4 view;
uniform mat4 projection;
uniform vec3 viewPos;


out vec3 pInfo;
uniform float PARTICLE_RADIUS;

void main()
{
    Particle p = particles[gl_VertexID];

    gl_Position = projection * view * vec4(p.position_stress.xyz, 1.0);

    float dist_to_camera = length(viewPos - p.position_stress.xyz);
    float base_size = 2000. * ( PARTICLE_RADIUS * p.position_stress.w + PARTICLE_RADIUS);
    gl_PointSize = base_size / (dist_to_camera);
    gl_PointSize = clamp(gl_PointSize, 2.0, base_size);
    pInfo = vec3(p.velocity_type.w, p.position_stress.w, dist_to_camera);
}
