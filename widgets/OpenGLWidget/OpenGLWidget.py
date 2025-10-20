"""
Widget OpenGL
"""
import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from .modules import Camera,ShaderManager,ColormapManager,BufferManager,Renderer

class OpenGLWidget(QOpenGLWidget):
    """Widget OpenGL para visualización de modelos 3D"""
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.shader_manager = ShaderManager()
        self.colormap_manager = ColormapManager()
        self.buffer_manager = BufferManager()
        self.renderer = Renderer(self.shader_manager, self.buffer_manager, self.colormap_manager)
        
        # Datos de geometría
        self.triangle_indices = None
        self.line_indices = None
        self.coords = None
        
        # Cámara
        self.camera = None
        
        # Estado
        self.last_x = 0
        self.last_y = 0
        self.current_mode = "solid"
        
        # Flags
        self.gl_initialized = False
        self.geometry_initialized = False
        
        self._setup_opengl_format()
    
    def _setup_opengl_format(self):
        """Configura el formato OpenGL"""
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
    
    def initialize_geometry(self, coords, triangle_indices, line_indices):
        """Inicializa la geometría del modelo"""
        self.coords = coords
        self.triangle_indices = triangle_indices
        self.line_indices = line_indices
        
        # Si OpenGL ya está inicializado, crear buffers inmediatamente
        if self.gl_initialized:
            self._initialize_buffers_and_camera()
        
        self.geometry_initialized = True
        return self
    
    def _initialize_buffers_and_camera(self):
        """Inicializa buffers y cámara (llamado cuando ambos GL y geometría están listos)"""
        if not self.geometry_initialized:
            raise RuntimeError("Geometría no inicializada. Llame a initialize_geometry() primero.")
        
        self.buffer_manager.initialize(self.coords, self.triangle_indices, self.line_indices)
        self.buffer_manager.create_all_buffers()
        self._setup_camera()
        
        coords = self.buffer_manager.get_coords()
        print(f"Buffers creados. Vértices: {len(coords)}, "
              f"Triángulos: {len(self.buffer_manager.triangle_indices)//3}, "
              f"Líneas: {len(self.buffer_manager.line_indices)//2}")
    
    def initializeGL(self):
        """Inicializa OpenGL"""
        print("Inicializando OpenGL...")
        
        # Configurar OpenGL
        self.renderer.setup_opengl()
        
        # Crear recursos de shaders y texturas
        self.shader_manager.compile_all()
        self.colormap_manager.create_texture()
        
        self.gl_initialized = True
        
        if self.geometry_initialized:
            self._initialize_buffers_and_camera()
        
        self.set_line_color((1.0,0.0,0.0,1.0))
        self.set_bg_color((0.098, 0.098, 0.098))
        self.set_solid_color((0.196, 0.196, 0.196, 1.0))
        
        print("Inicialización OpenGL completa")
    
    def _setup_camera(self):
        """Configura la cámara basada en el modelo"""
        coords = self.buffer_manager.get_coords()
        model_center = coords.mean(axis=0)
        distances = np.linalg.norm(coords - model_center, axis=1)
        model_radius = max(distances.max() * 1.5, 1.0)
        self.camera = Camera(model_center, model_radius)
    
    def paintGL(self):
        """Renderiza la escena"""
        if not self.camera or not self.geometry_initialized:
            return
        
        mvp_matrix = self._calculate_mvp_matrix()
        self.renderer.render_scene(
            self.current_mode,
            mvp_matrix,
            self.width(),
            self.height()
        )
    
    def _calculate_mvp_matrix(self):
        """Calcula la matriz MVP"""
        width, height = self.width(), max(self.height(), 1)
        ratio = width / height
        
        view = self.camera.get_view_matrix()
        proj = Matrix44.perspective_projection(45.0, ratio, 0.1, self.camera.radius * 10.0)
        return (proj * view).astype(np.float32)
    
    def resizeGL(self, w, h):
        """Maneja el redimensionamiento del widget"""
        glViewport(0, 0, w, h)
    
    # ============ Eventos de Mouse ============
    
    def mousePressEvent(self, event):
        """Maneja el evento de presión del mouse"""
        self.last_x = event.position().x()
        self.last_y = event.position().y()
    
    def mouseMoveEvent(self, event):
        """Maneja el movimiento del mouse"""
        if not self.camera:
            return
        
        x, y = event.position().x(), event.position().y()
        dx, dy = x - self.last_x, y - self.last_y
        self.last_x, self.last_y = x, y
        
        buttons = event.buttons()
        if buttons & Qt.MouseButton.LeftButton:
            self.camera.rotate(dx, dy)
            self.update()
        elif buttons & Qt.MouseButton.RightButton:
            self.camera.pan(dx, dy)
            self.update()
    
    def wheelEvent(self, event):
        """Maneja el evento de la rueda del mouse"""
        if self.camera:
            delta = event.angleDelta().y() / 120
            if delta != 0:
                self.camera.zoom(delta)
                self.update()
    
    # ============ API Pública ============
    
    def set_mode(self, mode):
        """Establece el modo de renderizado"""
        if mode in ["solid", "wireframe", "combined"]:
            self.current_mode = mode
            self.update()
    
    def set_line_width(self, width):
        """Establece el grosor de línea"""
        self.renderer.set_line_width(width)
        self.update()
        
    def set_line_color(self,color):
        """Establece el color de línea"""
        self.renderer.set_line_color(color)
        self.update()
        
    def set_solid_color(self,color):
        """Establece el color de solid"""
        self.renderer.set_solid_color(color)
        self.update()   
    
    def set_bg_color(self, color):
        """Establece el color de fondo"""
        self.renderer.set_bg_color(color)
        self.update()
    
    def reset_camera(self):
        """Resetea la cámara a su posición inicial"""
        if self.camera:
            self.camera.reset()
            self.update()
    
    # ============ Gestión de Gradientes ============
    
    def set_node_values(self, values, auto_range=True):
        """Establece los valores nodales para el gradiente"""
        if not self.geometry_initialized:
            print("Geometría no inicializada todavía")
            return
        
        values_array = np.asarray(values, dtype=np.float32)
        
        if not self.buffer_manager.update_gradient_values(values_array):
            return
        
        if auto_range:
            value_min = float(np.min(values_array))
            value_max = float(np.max(values_array))
            
            if abs(value_max - value_min) < 1e-10:
                value_max = value_min + 1.0
            
            self.renderer.set_value_range(value_min, value_max)
        
        self.update()
    
    def set_color_palette(self, palette_name):
        """Cambia la paleta de colores."""
        if self.colormap_manager.set_palette(palette_name):
            self.update()
    
    def enable_gradient(self, enabled=True):
        """Habilita o deshabilita el renderizado con gradientes."""
        self.renderer.set_gradient_enabled(enabled)
        self.update()
    
    def is_gradient_enabled(self):
        """Retorna si el gradiente está habilitado"""
        return self.renderer.is_gradient_enabled()
    
    def get_available_palettes(self):
        """Retorna la lista de paletas disponibles"""
        return self.colormap_manager.get_available_palettes()
    
    def get_value_range(self):
        """Retorna el rango de valores actual (min, max)"""
        return self.renderer.get_value_range()
    
    # ============ Actualización de Geometría ============
    
    def update_coords(self, new_coords):
        """Actualiza solo las coordenadas de los vértices."""
        if not self.geometry_initialized:
            print("Geometría no inicializada todavía")
            return
        
        if not self.gl_initialized:
            print("OpenGL no está inicializado todavía")
            return
        
        if self.buffer_manager.update_coords(new_coords):
            self.update()
    
    def update_camera_for_current_model(self):
        """Recalcula la cámara para el modelo actual"""
        if self.gl_initialized and self.geometry_initialized:
            self._setup_camera()
            self.update()
    
    # ============ Limpieza ============
    
    def __del__(self):
        """Limpieza de recursos OpenGL"""
        if hasattr(self, 'gl_initialized') and self.gl_initialized:
            self.cleanup()
    
    def cleanup(self):
        """Limpia todos los recursos OpenGL"""
        try:
            self.buffer_manager.cleanup()
            self.colormap_manager.cleanup()
            print("Recursos OpenGL liberados")
        except:
            pass