#version 450 core


struct Particle {
    vec3 position;
    vec4 velocity_type;
};

layout(std430, binding = 0) buffer ParticleBuffer { Particle particles[]; };
layout(std430, binding = 1) buffer GridHead { int gridHead[]; };
layout(std430, binding = 2) buffer ParticleLinks { int particleLinks[]; };

uniform mat4 view;
uniform mat4 projection;
uniform vec3 viewPos;

uniform int ACTIVE_TYPES;

uniform float cellSize;
uniform int PARTICLE_COUNT;
uniform int gridSize;

in vec2 TexCoords;
out vec4 FragColor;
in float vType;

const int MAX_ITERATIONS = 500;
const float MAX_DISTANCE = 150.0;
const float SURFACE_THRESHOLD = 0.01;

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float smoothMin(float distA, float distB, float smoothing){
    float h = max(smoothing - abs(distA-distB), 0.0) / smoothing;
    return min(distA, distB) - h*h*h*smoothing*(1.0/6.0);
}

float sdSphere(vec3 p, vec3 center, float radius)
{
    return length(p - center) - radius;
}


vec2 performRayMarching(vec3 rayOrigin, vec3 rayDirection)
{
    float totalDistance = 0.0;
    float particlesFound = 0.0;
    float minDist = MAX_DISTANCE;
    float dist = MAX_DISTANCE;
    float typeFound = 0.;
    int ITS = MAX_ITERATIONS;
    for (int i = 0; i < MAX_ITERATIONS; ++i)
    {
        vec3 currentPosition = rayOrigin + rayDirection * totalDistance;
        ivec3 cell = ivec3(floor((currentPosition + 1.0) / cellSize));
        if (any(lessThan(cell, ivec3(0))) || any(greaterThanEqual(cell, ivec3(gridSize)))) {
            break;
        }
        int cellIdx = (cell.z * gridSize * gridSize) + (cell.y * gridSize) + cell.x;
        int head = gridHead[cellIdx];

        while (head != -1) {

            Particle p = particles[head];
            dist = sdSphere(currentPosition, p.position, 0.005);

            if (dist < minDist) {
                typeFound = p.velocity_type.w;
            }
            minDist = smoothMin(dist, minDist, 0.1);



            
  
            

            head = particleLinks[head];

        }

        if (minDist < SURFACE_THRESHOLD) {
            return vec2(minDist, typeFound);

        }

        totalDistance += minDist;

    }
    return vec2(-1.0, -1.0); 
}

void main() {
    vec2 ndc = TexCoords * 2.0 - 1.0;

    // Inverse projection and view to get world ray
    mat4 invProj = inverse(projection);
    mat4 invView = inverse(view);

    // Start at camera position in world space
    vec4 camPos4 = invView * vec4(0.0, 0.0, 0.0, 1.0);
    vec3 rayOrigin = camPos4.xyz / camPos4.w;

    // Compute ray direction in world space
    vec4 target = invProj * vec4(ndc, 1.0, 1.0);
    target /= target.w;
    vec4 worldTarget = invView * vec4(target.xyz, 1.0);
    vec3 rayDir = normalize(worldTarget.xyz - rayOrigin);

    // Perform raymarching with world-space origin and direction
    vec2 scene = performRayMarching(rayOrigin, rayDir);
    if (scene.x > -1.0) {
        float typeIdx = clamp(scene.y, 0.0, float(ACTIVE_TYPES - 1));
        float hue = typeIdx / float(ACTIVE_TYPES); 
        vec3 baseColor = hsv2rgb(vec3(hue, 0.7, 1.8));

        FragColor = vec4(baseColor * vec3(1. - scene.x), 1.0);
    } else {
        discard;
        
    }  
}