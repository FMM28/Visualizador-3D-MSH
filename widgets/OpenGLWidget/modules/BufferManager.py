"""
Módulo para gestión de buffers OpenGL
"""
import numpy as np
from OpenGL.GL import *

class BufferManager:
    """Gestiona los buffers OpenGL (VAO, VBO, IBO)"""
    
    def __init__(self):
        self.coords_array = None
        self.triangle_indices = None
        self.line_indices = None
        self.line_vertices_buffer = None
        self.buffers = self._init_buffer_structure()
    
    def _init_buffer_structure(self):
        """Inicializa la estructura de buffers"""
        return {
            'solid': {'vao': None, 'vbo': None, 'ibo': None, 'count': 0},
            'line': {'vao': None, 'vbo': None, 'count': 0},
            'gradient': {'vao': None, 'vbo_pos': None, 'vbo_val': None, 'ibo': None, 'count': 0}
        }
    
    def initialize(self, coords, triangle_indices, line_indices):
        """Inicializa el BufferManager con los datos de la geometría"""
        self.coords_array = np.asarray(coords, dtype=np.float32)
        self.triangle_indices = np.asarray(triangle_indices, dtype=np.uint32)
        self.line_indices = np.asarray(line_indices, dtype=np.uint32)
        return self
    
    def create_all_buffers(self):
        """Crea todos los buffers OpenGL"""
        if self.coords_array is None or self.triangle_indices is None or self.line_indices is None:
            raise RuntimeError("BufferManager no ha sido inicializado. Llame a initialize() primero.")
        
        self._prepare_line_buffer()
        self._create_solid_buffers()
        self._create_line_buffers()
        self._create_gradient_buffers()
        glBindVertexArray(0)
        print("Buffers creados exitosamente")
    
    def _prepare_line_buffer(self):
        """Prepara el buffer de vértices para líneas"""
        self.line_vertices_buffer = np.zeros(len(self.line_indices) * 3, dtype=np.float32)
        self._update_line_vertices_buffer()
    
    def _update_line_vertices_buffer(self):
        """Actualiza el buffer de vértices de líneas basado en coordenadas actuales"""
        coords_flat = self.coords_array[self.line_indices].flatten()
        self.line_vertices_buffer[:] = coords_flat
    
    def _create_solid_buffers(self):
        """Crea buffers para renderizado sólido"""
        solid_buf = self.buffers['solid']
        solid_buf['vao'] = glGenVertexArrays(1)
        solid_buf['vbo'] = glGenBuffers(1)
        solid_buf['ibo'] = glGenBuffers(1)
        solid_buf['count'] = len(self.triangle_indices)
        
        glBindVertexArray(solid_buf['vao'])
        
        # VBO coordenadas
        glBindBuffer(GL_ARRAY_BUFFER, solid_buf['vbo'])
        glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # IBO índices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, solid_buf['ibo'])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangle_indices.nbytes, self.triangle_indices, GL_STATIC_DRAW)
    
    def _create_line_buffers(self):
        """Crea buffers para renderizado de líneas"""
        line_buf = self.buffers['line']
        line_buf['vao'] = glGenVertexArrays(1)
        line_buf['vbo'] = glGenBuffers(1)
        line_buf['count'] = len(self.line_indices)
        
        glBindVertexArray(line_buf['vao'])
        glBindBuffer(GL_ARRAY_BUFFER, line_buf['vbo'])
        glBufferData(GL_ARRAY_BUFFER, self.line_vertices_buffer.nbytes, self.line_vertices_buffer, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
    
    def _create_gradient_buffers(self):
        """Crea buffers para renderizado con gradientes"""
        grad_buf = self.buffers['gradient']
        grad_buf['vao'] = glGenVertexArrays(1)
        grad_buf['vbo_pos'] = glGenBuffers(1)
        grad_buf['vbo_val'] = glGenBuffers(1)
        grad_buf['ibo'] = glGenBuffers(1)
        grad_buf['count'] = len(self.triangle_indices)
        
        glBindVertexArray(grad_buf['vao'])
        
        # VBO coordenadas
        glBindBuffer(GL_ARRAY_BUFFER, grad_buf['vbo_pos'])
        glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # VBO valores (inicialmente vacío)
        glBindBuffer(GL_ARRAY_BUFFER, grad_buf['vbo_val'])
        dummy_values = np.zeros(len(self.coords_array), dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, dummy_values.nbytes, dummy_values, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        
        # IBO índices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, grad_buf['ibo'])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangle_indices.nbytes, self.triangle_indices, GL_STATIC_DRAW)
    
    def update_coords(self, new_coords):
        """Actualiza las coordenadas de los vértices"""
        if self.coords_array is None:
            raise RuntimeError("BufferManager no ha sido inicializado.")
        
        new_coords_array = np.asarray(new_coords, dtype=np.float32)
        if new_coords_array.shape != self.coords_array.shape:
            print(f"Error: Las nuevas coordenadas deben tener la misma forma que las originales")
            print(f"Original: {self.coords_array.shape}, Nueva: {new_coords_array.shape}")
            return False
        
        # Actualizar coordenadas
        self.coords_array[:] = new_coords_array
        
        # Actualizar buffer sólido
        glBindBuffer(GL_ARRAY_BUFFER, self.buffers['solid']['vbo'])
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.coords_array.nbytes, self.coords_array)
        
        # Actualizar buffer de gradientes
        glBindBuffer(GL_ARRAY_BUFFER, self.buffers['gradient']['vbo_pos'])
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.coords_array.nbytes, self.coords_array)
        
        # Actualizar buffer de líneas
        self._update_line_vertices_buffer()
        glBindBuffer(GL_ARRAY_BUFFER, self.buffers['line']['vbo'])
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.line_vertices_buffer.nbytes, self.line_vertices_buffer)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return True
    
    def update_gradient_values(self, values):
        """Actualiza los valores del gradiente"""
        if self.coords_array is None:
            raise RuntimeError("BufferManager no ha sido inicializado.")
        
        values_array = np.asarray(values, dtype=np.float32)
        
        if len(values_array) != len(self.coords_array):
            print(f"Error: Se esperan {len(self.coords_array)} valores, se recibieron {len(values_array)}")
            return False
        
        glBindBuffer(GL_ARRAY_BUFFER, self.buffers['gradient']['vbo_val'])
        glBufferSubData(GL_ARRAY_BUFFER, 0, values_array.nbytes, values_array)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return True
    
    def get_buffer(self, buffer_type):
        """Obtiene información de un buffer específico"""
        return self.buffers.get(buffer_type)
    
    def get_coords(self):
        """Obtiene las coordenadas actuales"""
        return self.coords_array
    
    def cleanup(self):
        """Limpia los recursos OpenGL"""
        try:
            for buf_type in self.buffers.values():
                if buf_type.get('vao'):
                    glDeleteVertexArrays(1, [buf_type['vao']])
                if buf_type.get('vbo'):
                    glDeleteBuffers(1, [buf_type['vbo']])
                if buf_type.get('vbo_pos'):
                    glDeleteBuffers(1, [buf_type['vbo_pos']])
                if buf_type.get('vbo_val'):
                    glDeleteBuffers(1, [buf_type['vbo_val']])
                if buf_type.get('ibo'):
                    glDeleteBuffers(1, [buf_type['ibo']])
        except:
            pass