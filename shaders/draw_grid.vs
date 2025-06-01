#version 450


uniform mat4 view;
uniform mat4 projection;
uniform vec3 viewPos;

const float GRID_SIZE = 800.0; 
out vec3 worldPos;

const vec3 Pos[4] = vec3[4](
    vec3(-1.0,  0.0, -1.0), // Bottom left
    vec3( 1.0,  0.0, -1.0), // Bottom right
    vec3( 1.0,  0.0,  1.0), // Top right
    vec3(-1.0,  0.0,  1.0)  // Top left
);

const int Indices[6] = int[6](
    0, 1, 2,
    2, 0, 3
);


void main()
{
    int Index = Indices[gl_VertexID];
    vec3 vPos = Pos[Index] * GRID_SIZE - vec3(0.,150. * 0.5,0.);
    vPos.x += viewPos.x;
    vPos.z += viewPos.z;
    vec4 vPos4 = vec4(vPos, 1.0);
    gl_Position = projection * view  * vPos4;
    worldPos = vPos;
}