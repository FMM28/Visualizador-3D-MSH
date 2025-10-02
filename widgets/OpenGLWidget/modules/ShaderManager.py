"""
Módulo para gestión de shaders
"""
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

class ShaderManager:
    """Gestiona la compilación y uso de shaders"""
    
    # Vertex Shaders
    VERTEX_SHADER = """
    #version 330 core
    uniform mat4 mvp;
    layout(location = 0) in vec3 in_position;
    void main() {
        gl_Position = mvp * vec4(in_position, 1.0);
    }
    """
    
    VERTEX_SHADER_GRADIENT = """
    #version 330 core
    uniform mat4 mvp;
    layout(location = 0) in vec3 in_position;
    layout(location = 1) in float in_value;
    out float frag_value;
    void main() {
        gl_Position = mvp * vec4(in_position, 1.0);
        frag_value = in_value;
    }
    """
    
    # Geometry Shader
    GEOMETRY_SHADER = """
    #version 330 core
    layout(lines) in;
    layout(triangle_strip, max_vertices = 4) out;
    
    uniform float line_width;
    uniform float aspect_ratio;
    
    void main() {
        vec4 p0 = gl_in[0].gl_Position;
        vec4 p1 = gl_in[1].gl_Position;
        
        if (abs(p0.w) < 1e-6 || abs(p1.w) < 1e-6) return;
        
        vec3 ndc0 = p0.xyz / p0.w;
        vec3 ndc1 = p1.xyz / p1.w;
        
        vec2 dir = ndc1.xy - ndc0.xy;
        float len_dir = length(dir);
        if (len_dir < 1e-6) return;
        
        dir /= len_dir;
        vec2 normal = normalize(vec2(-dir.y, dir.x / aspect_ratio)) * line_width * 0.002;
        
        gl_Position = vec4((ndc0.xy - normal) * p0.w, p0.z, p0.w); EmitVertex();
        gl_Position = vec4((ndc0.xy + normal) * p0.w, p0.z, p0.w); EmitVertex();
        gl_Position = vec4((ndc1.xy - normal) * p1.w, p1.z, p1.w); EmitVertex();
        gl_Position = vec4((ndc1.xy + normal) * p1.w, p1.z, p1.w); EmitVertex();
        EndPrimitive();
    }
    """
    
    # Fragment Shaders
    FRAGMENT_SHADER_SOLID = """
    #version 330 core
    out vec4 frag_color;
    void main() {
        frag_color = vec4(0.2, 0.2, 0.2, 1.0);
    }
    """
    
    FRAGMENT_SHADER_LINE = """
    #version 330 core
    out vec4 frag_color;
    void main() {
        frag_color = vec4(1.0, 0.2, 0.2, 1.0);
    }
    """
    
    FRAGMENT_SHADER_GRADIENT = """
    #version 330 core
    in float frag_value;
    out vec4 frag_color;
    
    uniform sampler1D colormap;
    uniform float value_min;
    uniform float value_max;
    
    void main() {
        float t = clamp((frag_value - value_min) / (value_max - value_min), 0.0, 1.0);
        frag_color = texture(colormap, t);
    }
    """
    
    def __init__(self):
        self.programs = {}
    
    def compile_all(self):
        """Compila todos los programas de shaders"""
        try:
            vs = compileShader(self.VERTEX_SHADER, GL_VERTEX_SHADER)
            
            # Shader sólido
            fs_solid = compileShader(self.FRAGMENT_SHADER_SOLID, GL_FRAGMENT_SHADER)
            self.programs["solid"] = compileProgram(vs, fs_solid)
            
            # Shader de líneas con geometry shader
            gs = compileShader(self.GEOMETRY_SHADER, GL_GEOMETRY_SHADER)
            fs_line = compileShader(self.FRAGMENT_SHADER_LINE, GL_FRAGMENT_SHADER)
            self.programs["line"] = compileProgram(vs, gs, fs_line)
            
            # Shader de gradientes
            vs_grad = compileShader(self.VERTEX_SHADER_GRADIENT, GL_VERTEX_SHADER)
            fs_grad = compileShader(self.FRAGMENT_SHADER_GRADIENT, GL_FRAGMENT_SHADER)
            self.programs["gradient"] = compileProgram(vs_grad, fs_grad)
            
            print("Shaders compilados exitosamente")
            
        except Exception as e:
            print(f"Error compilando shaders: {e}")
            raise
    
    def get_program(self, name):
        """Obtiene un programa de shader por nombre"""
        return self.programs.get(name)
    
    def use_program(self, name):
        """Activa un programa de shader"""
        program = self.programs.get(name)
        if program:
            glUseProgram(program)
            return program
        return None
    
    def set_uniform_matrix4fv(self, program, name, matrix):
        """Establece un uniform de tipo mat4"""
        loc = glGetUniformLocation(program, name)
        if loc != -1:
            glUniformMatrix4fv(loc, 1, GL_FALSE, matrix)
    
    def set_uniform_1f(self, program, name, value):
        """Establece un uniform de tipo float"""
        loc = glGetUniformLocation(program, name)
        if loc != -1:
            glUniform1f(loc, value)
    
    def set_uniform_1i(self, program, name, value):
        """Establece un uniform de tipo int"""
        loc = glGetUniformLocation(program, name)
        if loc != -1:
            glUniform1i(loc, value)