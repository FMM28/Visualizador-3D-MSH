"""
Módulo para renderizado OpenGL
"""
from OpenGL.GL import *

class Renderer:
    """Gestiona el renderizado de la escena"""
    
    def __init__(self, shader_manager, buffer_manager, colormap_manager):
        self.shader_manager = shader_manager
        self.buffer_manager = buffer_manager
        self.colormap_manager = colormap_manager
        
        self.line_width = 1.0
        self.bg_color = (0.1, 0.1, 0.1)
        
        # Estado de gradientes
        self.gradient_enabled = False
        self.value_min = 0.0
        self.value_max = 1.0
    
    def setup_opengl(self):
        """Configura el estado inicial de OpenGL"""
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_POLYGON_OFFSET_FILL)
    
    def clear_screen(self):
        """Limpia los buffers de color y profundidad"""
        glClearColor(*self.bg_color, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    def render_solid(self, mvp_matrix):
        """Renderiza el modelo sólido"""
        glPolygonOffset(1.0, 1.0)
        glEnable(GL_POLYGON_OFFSET_FILL)
        
        program = self.shader_manager.use_program("solid")
        if not program:
            return
        
        self.shader_manager.set_uniform_matrix4fv(program, "mvp", mvp_matrix)
        
        buf = self.buffer_manager.get_buffer('solid')
        glBindVertexArray(buf['vao'])
        glDrawElements(GL_TRIANGLES, buf['count'], GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def render_gradient(self, mvp_matrix):
        """Renderiza el modelo con gradientes"""
        if not self.gradient_enabled:
            self.render_solid(mvp_matrix)
            return
        
        glPolygonOffset(1.0, 1.0)
        glEnable(GL_POLYGON_OFFSET_FILL)
        
        program = self.shader_manager.use_program("gradient")
        if not program:
            return
        
        # Configurar uniformes
        self.shader_manager.set_uniform_matrix4fv(program, "mvp", mvp_matrix)
        
        # Configurar textura de colormap
        self.colormap_manager.bind_texture(0)
        self.shader_manager.set_uniform_1i(program, "colormap", 0)
        
        # Configurar rango de valores
        self.shader_manager.set_uniform_1f(program, "value_min", self.value_min)
        self.shader_manager.set_uniform_1f(program, "value_max", self.value_max)
        
        buf = self.buffer_manager.get_buffer('gradient')
        glBindVertexArray(buf['vao'])
        glDrawElements(GL_TRIANGLES, buf['count'], GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def render_wireframe(self, mvp_matrix, viewport_width, viewport_height):
        """Renderiza el modelo en alambre"""
        glDisable(GL_POLYGON_OFFSET_FILL)
        
        program = self.shader_manager.use_program("line")
        if not program:
            return
        
        self.shader_manager.set_uniform_matrix4fv(program, "mvp", mvp_matrix)
        self.shader_manager.set_uniform_1f(program, "line_width", self.line_width)
        
        aspect = viewport_width / max(viewport_height, 1)
        self.shader_manager.set_uniform_1f(program, "aspect_ratio", aspect)
        
        buf = self.buffer_manager.get_buffer('line')
        glBindVertexArray(buf['vao'])
        glDrawArrays(GL_LINES, 0, buf['count'])
        glBindVertexArray(0)
    
    def render_scene(self, mode, mvp_matrix, viewport_width, viewport_height):
        """Renderiza la escena completa según el modo especificado"""
        self.clear_screen()
        
        if mode == "solid":
            if self.gradient_enabled:
                self.render_gradient(mvp_matrix)
            else:
                self.render_solid(mvp_matrix)
        
        elif mode == "wireframe":
            self.render_wireframe(mvp_matrix, viewport_width, viewport_height)
        
        elif mode == "combined":
            if self.gradient_enabled:
                self.render_gradient(mvp_matrix)
            else:
                self.render_solid(mvp_matrix)
            
            glDepthMask(GL_FALSE)
            self.render_wireframe(mvp_matrix, viewport_width, viewport_height)
            glDepthMask(GL_TRUE)
    
    # Setters
    def set_line_width(self, width):
        """Establece el grosor de línea"""
        self.line_width = max(0.1, width)
    
    def set_bg_color(self, color):
        """Establece el color de fondo (tuple RGB)"""
        self.bg_color = color
    
    def set_gradient_enabled(self, enabled):
        """Habilita o deshabilita el renderizado con gradientes"""
        self.gradient_enabled = enabled
    
    def set_value_range(self, min_val, max_val):
        """Establece el rango de valores para el gradiente"""
        self.value_min = float(min_val)
        self.value_max = float(max_val)
        if abs(self.value_max - self.value_min) < 1e-10:
            self.value_max = self.value_min + 1.0
    
    # Getters
    def is_gradient_enabled(self):
        """Retorna si el gradiente está habilitado"""
        return self.gradient_enabled
    
    def get_value_range(self):
        """Retorna el rango de valores actual"""
        return (self.value_min, self.value_max)