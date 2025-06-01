#version 450

in vec3 worldPos;
out vec4 FragColor;
uniform vec2 uViewport;

const float GRID_SIZE = 800.0; 
const float gridCellSize = 0.1; // Size of each grid cell
const float gridMinPixelsBetweenCells = 5.0; 
const vec4 gridColorThin = vec4(vec3(0.1), 1.); 
const vec4 gridColorThick = vec4(vec3(0.15), 1.0); 
uniform vec3 viewPos;   

float log10(float x) {
    return log(x) / log(10.0);
}



void main() {

    vec2 dvx = vec2(dFdx(worldPos.x), dFdy(worldPos.x));
    vec2 dvy = vec2(dFdx(worldPos.z), dFdy(worldPos.z));

    float lx = length(dvx) + 0.000001;
    float ly = length(dvy) + 0.000001;

    vec2 dudv = vec2(lx,ly);



    float l = length(dudv) ;



    float LOD = max(0., log10(l * gridMinPixelsBetweenCells / gridCellSize) + 1.);

    float gridCellSizeLod0 = gridCellSize * pow(10., floor(LOD));
    float gridCellSizeLod1 = gridCellSizeLod0 * 10.;
    float gridCellSizeLod2 = gridCellSizeLod1 * 10.;

    dudv *= 4.;

    vec2 Lod0axy = mod(worldPos.xz, gridCellSizeLod0) / dudv;
    vec2 Lod1axy = mod(worldPos.xz, gridCellSizeLod1) / dudv;
    vec2 Lod2axy = mod(worldPos.xz, gridCellSizeLod2) / dudv;

    Lod0axy = vec2(1.) - (clamp(abs(Lod0axy),0.,1.) * 2. - vec2(1.)); 
    Lod1axy = vec2(1.) - (clamp(abs(Lod1axy),0.,1.) * 2. - vec2(1.)); 
    Lod2axy = vec2(1.) - (clamp(abs(Lod2axy),0.,1.) * 2. - vec2(1.)); 

    float Lod0a = max(Lod0axy.x, Lod0axy.y);
    float Lod1a = max(Lod1axy.x, Lod1axy.y);
    float Lod2a = max(Lod2axy.x, Lod2axy.y);

    float LOD_fade = fract(LOD);
    float OpacityFalloff= (1. - length(worldPos.xz - viewPos.xz)/ GRID_SIZE); 
    vec4 color;
    if (Lod2a > 0.)
    {   
        color = gridColorThick;
        color.a *= OpacityFalloff;
    } else {
        if (Lod1a > 0.)
        {
            color = mix(gridColorThick, gridColorThin, LOD_fade);
        } else {
            color = gridColorThin; 
            color.a *= (Lod0a * (1. - LOD_fade));
        }
    }

    
    color.a *= OpacityFalloff;
    FragColor = color; 
}