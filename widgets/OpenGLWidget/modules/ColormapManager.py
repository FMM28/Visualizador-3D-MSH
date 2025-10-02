"""
Módulo para gestión de mapas de colores
"""
import numpy as np
from OpenGL.GL import *

class ColormapManager:
    """Gestiona las paletas de colores y texturas 1D"""
    
    COLOR_PALETTES = {
        "viridis": [
            (0.267004, 0.004874, 0.329415),
            (0.282623, 0.140926, 0.457517),
            (0.253935, 0.265254, 0.529983),
            (0.206756, 0.371758, 0.553117),
            (0.163625, 0.471133, 0.558148),
            (0.127568, 0.566949, 0.550556),
            (0.134692, 0.658636, 0.517649),
            (0.266941, 0.748751, 0.440573),
            (0.477504, 0.821444, 0.318195),
            (0.741388, 0.873449, 0.149561),
            (0.993248, 0.906157, 0.143936)
        ],
        "plasma": [
            (0.050383, 0.029803, 0.527975),
            (0.280264, 0.015654, 0.633301),
            (0.445680, 0.006352, 0.658034),
            (0.588235, 0.016658, 0.628050),
            (0.707188, 0.077863, 0.551710),
            (0.805257, 0.161158, 0.461497),
            (0.884850, 0.253522, 0.367040),
            (0.944006, 0.358379, 0.274460),
            (0.976853, 0.479434, 0.189503),
            (0.985673, 0.625984, 0.122738),
            (0.940015, 0.975158, 0.131326)
        ],
        "jet": [
            (0.0, 0.0, 0.5),
            (0.0, 0.0, 1.0),
            (0.0, 0.5, 1.0),
            (0.0, 1.0, 1.0),
            (0.5, 1.0, 0.5),
            (1.0, 1.0, 0.0),
            (1.0, 0.5, 0.0),
            (1.0, 0.0, 0.0),
            (0.5, 0.0, 0.0)
        ],
        "coolwarm": [
            (0.230, 0.299, 0.754),
            (0.706, 0.016, 0.150),
        ],
        "rainbow": [
            (0.5, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 1.0, 1.0),
            (0.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 0.0, 0.0)
        ],
        "grayscale": [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0)
        ]
    }
    
    def __init__(self):
        self.texture = None
        self.current_palette = "viridis"
        self.num_colors = 256
    
    def create_texture(self):
        """Crea la textura 1D para el mapa de colores"""
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self.texture)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        self.update_texture()
    
    def update_texture(self):
        """Actualiza la textura con la paleta actual"""
        palette = self.COLOR_PALETTES.get(self.current_palette, self.COLOR_PALETTES["viridis"])
        
        # Interpolar la paleta a 256 colores
        palette_array = np.array(palette, dtype=np.float32)
        
        # Crear interpolación
        t = np.linspace(0, 1, self.num_colors)
        palette_t = np.linspace(0, 1, len(palette))
        
        colors = np.zeros((self.num_colors, 3), dtype=np.float32)
        for i in range(3):  # R, G, B
            colors[:, i] = np.interp(t, palette_t, palette_array[:, i])
        
        # Subir a GPU
        glBindTexture(GL_TEXTURE_1D, self.texture)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGB32F, self.num_colors, 0, GL_RGB, GL_FLOAT, colors)
    
    def set_palette(self, palette_name):
        """Cambia la paleta de colores"""
        if palette_name in self.COLOR_PALETTES:
            self.current_palette = palette_name
            if self.texture:
                self.update_texture()
            return True
        return False
    
    def get_available_palettes(self):
        """Retorna la lista de paletas disponibles"""
        return list(self.COLOR_PALETTES.keys())
    
    def bind_texture(self, texture_unit=0):
        """Enlaza la textura a una unidad de textura"""
        if self.texture:
            glActiveTexture(GL_TEXTURE0 + texture_unit)
            glBindTexture(GL_TEXTURE_1D, self.texture)
    
    def cleanup(self):
        """Limpia los recursos OpenGL"""
        if self.texture:
            glDeleteTextures(1, [self.texture])
            self.texture = None