#version 450


in vec3 pInfo;

out vec4 FragColor;
uniform vec2 uViewport;
uniform int ACTIVE_TYPES;
uniform float PARTICLE_RADIUS;

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}



void main() {
    vec2 c = gl_PointCoord - vec2(0.5);
    float aspect = uViewport.x / uViewport.y;
    c.x *= aspect;
    c.y *= aspect;

    float vType = pInfo.x;
    float vStress = pInfo.y;    
    float vDist = pInfo.z;


    float dist_sq = dot(c, c);

    float alpha = pow(smoothstep(0.1, 0.0, dist_sq), 2.0); 
    if (alpha < 0.01) discard;
    
    float typeIdx = clamp(vType, 0.0, float(ACTIVE_TYPES - 1));
    float hue = typeIdx / float(ACTIVE_TYPES); 
    float brightness = 0.8 + vStress * 2.  ;
    vec3 baseColor = hsv2rgb(vec3(hue, 0.7, brightness));



    FragColor = vec4(baseColor * alpha,  1.);
}
