"""
Widget OpenGL
"""
import numpy as np
from OpenGL.GL import *
from PyQt6 import sip
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QImage, QPainter, QRegion, QSurfaceFormat
from PyQt6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QWidget

import utils.Matrix44 as Matrix44

from .modules import (
    BufferManager,
    Camera,
    ColorBar,
    ColormapManager,
    Renderer,
    ShaderManager,
)


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
        self.current_mode = "combined"
        
        # Flags
        self.gl_initialized = False
        self.geometry_initialized = False
        self.buffers_created = False
        self._has_gradient_range = False
        
        # Barra de colores superpuesta
        self.color_bar = ColorBar(self)
        self.color_bar.set_colors(
            self.colormap_manager.get_palette_colors(self.colormap_manager.current_palette)
        )
        
        self._setup_opengl_format()
    
    def _setup_opengl_format(self):
        """Configura el formato OpenGL"""
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
    
    def initialize_geometry(self, coords, triangle_indices, line_indices, reset_camera=True):
        """Inicializa la geometría del modelo"""
        self.coords = coords
        self.triangle_indices = triangle_indices
        self.line_indices = line_indices
        
        self.geometry_initialized = True
        
        if self.gl_initialized:
            self.makeCurrent()
            self._initialize_buffers_and_camera(reset_camera)
            self.doneCurrent()
        
        return self
    
    def _initialize_buffers_and_camera(self, reset_camera=True):
        """Inicializa buffers y cámara (llamado cuando ambos GL y geometría están listos)"""
        if not self.geometry_initialized:
            raise RuntimeError("Geometría no inicializada. Llame a initialize_geometry() primero.")
        
        if not self.gl_initialized:
            print("Advertencia: OpenGL no inicializado todavía")
            return
        
        # Limpiar buffers anteriores si existen
        if self.buffers_created:
            self.buffer_manager.cleanup()
            self.buffers_created = False
        
        # Crear nuevos buffers
        self.buffer_manager.initialize(self.coords, self.triangle_indices, self.line_indices)
        self.buffer_manager.create_all_buffers()
        self.buffers_created = True
        
        # Solo resetear cámara si se solicita explícitamente
        if reset_camera:
            self._setup_camera()
        
        coords = self.buffer_manager.get_coords()
        print(f"Buffers creados. Vértices: {len(coords)}, "
              f"Triángulos: {len(self.buffer_manager.triangle_indices)//3}, "
              f"Líneas: {len(self.buffer_manager.line_indices)//2}")
        
        self.update()
    
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
            self._initialize_buffers_and_camera(reset_camera=True)
        
        self.set_line_color((1.0, 0.0, 0.0, 1.0))
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
        if not self.camera or not self.geometry_initialized or not self.buffers_created:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            return
        
        mvp_matrix = self._calculate_mvp_matrix()
        self.renderer.render_scene(
            self.current_mode,
            mvp_matrix,
            self.width(),
            self.height()
        )
    
    def _calculate_mvp_matrix(self, width=None, height=None):
        """Calcula la matriz MVP (por defecto con la proporción del widget)"""
        if width is None or height is None:
            width, height = self.width(), self.height()
        ratio = width / max(height, 1)
        
        view = self.camera.get_view_matrix()
        proj = Matrix44.perspective_projection(45.0, ratio, 0.1, self.camera.radius * 10.0)
        mvp = (view @ proj).astype(np.float32)
        return mvp
    
    def resizeGL(self, w, h):
        """Maneja el redimensionamiento del widget"""
        glViewport(0, 0, w, h)
        self.color_bar.reposition()
    
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
        if not self.geometry_initialized or not self.buffers_created:
            print("Geometría o buffers no inicializados todavía")
            return
        
        values_array = np.asarray(values, dtype=np.float32)
        
        self.makeCurrent()
        success = self.buffer_manager.update_gradient_values(values_array)
        self.doneCurrent()
        
        if not success:
            return
        
        if auto_range:
            value_min = float(np.min(values_array))
            value_max = float(np.max(values_array))
            
            # La barra muestra el rango real de los datos
            self.color_bar.set_range(value_min, value_max)
            self._has_gradient_range = True
            
            if abs(value_max - value_min) < 1e-10:
                value_max = value_min + 1.0
            
            self.renderer.set_value_range(value_min, value_max)
        
        self._update_color_bar_visibility()
        self.update()
    
    def set_colorbar_title(self, title):
        """Establece el título de la barra de colores"""
        self.color_bar.set_title(title)

    def set_colorbar_position(self, position):
        """Cambia la posición de la barra de colores ('right', 'top_left', ...)"""
        return self.color_bar.set_position(position)

    def get_colorbar_position(self):
        """Retorna la posición actual de la barra de colores"""
        return self.color_bar.position()
    
    def set_color_palette(self, palette_name):
        """Cambia la paleta de colores."""
        # La textura se sube a la GPU: requiere el contexto activo
        if self.gl_initialized:
            self.makeCurrent()
        success = self.colormap_manager.set_palette(palette_name)
        if self.gl_initialized:
            self.doneCurrent()
        
        if success:
            self.color_bar.set_colors(self.colormap_manager.get_palette_colors(palette_name))
            self.update()
    
    def enable_gradient(self, enabled=True):
        """Habilita o deshabilita el renderizado con gradientes."""
        self.renderer.set_gradient_enabled(enabled)
        self._update_color_bar_visibility()
        self.update()
    
    def _update_color_bar_visibility(self):
        """Muestra la barra solo si hay un gradiente activo con rango conocido"""
        visible = self.renderer.is_gradient_enabled() and self._has_gradient_range
        self.color_bar.setVisible(visible)
        if visible:
            self.color_bar.reposition()
            self.color_bar.raise_()
    
    def is_gradient_enabled(self):
        """Retorna si el gradiente está habilitado"""
        return self.renderer.is_gradient_enabled()
    
    def get_available_palettes(self):
        """Retorna la lista de paletas disponibles"""
        return self.colormap_manager.get_available_palettes()
    
    # ============ Actualización de Geometría ============
    
    def update_coords(self, new_coords):
        """Actualiza solo las coordenadas de los vértices."""
        if not self.geometry_initialized or not self.buffers_created:
            print("Geometría o buffers no inicializados todavía")
            return
        
        if not self.gl_initialized:
            print("OpenGL no está inicializado todavía")
            return
        
        self.makeCurrent()
        success = self.buffer_manager.update_coords(new_coords)
        self.doneCurrent()
        
        if success:
            self.update()
    
    # ============ Renderizado a imagen ============

    RENDER_SAMPLES = 4   # Antialiasing (MSAA) del render a imagen

    @staticmethod
    def _gl_int(param):
        """Lee un entero de glGetIntegerv (PyOpenGL puede devolver array o escalar)"""
        return int(np.ravel(glGetIntegerv(param))[0])

    def max_render_size(self):
        """Lado máximo en píxeles que la GPU admite para un render fuera de pantalla"""
        if not self.gl_initialized:
            return None
        self.makeCurrent()
        try:
            max_renderbuffer = self._gl_int(GL_MAX_RENDERBUFFER_SIZE)
            max_viewport = int(np.min(np.ravel(glGetIntegerv(GL_MAX_VIEWPORT_DIMS))))
        finally:
            self.doneCurrent()
        return min(max_renderbuffer, max_viewport)

    def render_to_image(self, width, height, include_color_bar=True):
        """
        Renderiza la escena fuera de pantalla a exactamente width x height píxeles,
        sin modificar el widget visible.
        """
        if not (self.gl_initialized and self.buffers_created and self.camera):
            raise RuntimeError("No hay un modelo cargado para renderizar.")

        width, height = int(width), int(height)
        limit = self.max_render_size()
        if width > limit or height > limit:
            raise ValueError(
                f"La tarjeta gráfica admite como máximo {limit} px por lado "
                f"(se pidió {width} x {height} px).")

        self.makeCurrent()
        fbo = None
        try:
            fmt = QOpenGLFramebufferObjectFormat()
            fmt.setAttachment(QOpenGLFramebufferObject.Attachment.CombinedDepthStencil)
            fmt.setSamples(min(self.RENDER_SAMPLES, self._gl_int(GL_MAX_SAMPLES)))

            fbo = QOpenGLFramebufferObject(width, height, fmt)
            if not fbo.isValid():
                raise RuntimeError(
                    f"No se pudo reservar memoria de vídeo para {width} x {height} px.")

            fbo.bind()
            glViewport(0, 0, width, height)
            mvp = self._calculate_mvp_matrix(width, height)
            self.renderer.render_scene(self.current_mode, mvp, width, height)
            image = fbo.toImage()   # Resuelve el multisampling y voltea a orientación Qt
            fbo.release()
        finally:
            if fbo is not None:
                sip.delete(fbo)     # Liberar la memoria de vídeo con el contexto activo
            glBindFramebuffer(GL_FRAMEBUFFER, self.defaultFramebufferObject())
            self.doneCurrent()

        image = image.convertToFormat(QImage.Format.Format_RGB32)
        if include_color_bar:
            self._paint_color_bar(image)
        return image

    def _paint_color_bar(self, image):
        """Pinta la barra de colores sobre la imagen con la misma escala relativa que en pantalla"""
        if not self.color_bar.isVisibleTo(self):
            return

        # Factor entre la imagen y el área visible: la barra ocupa la misma fracción
        scale = image.height() / max(self.height(), 1)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.scale(scale, scale)
        x, y = self.color_bar.aligned_position(image.width() / scale, image.height() / scale)
        # Sin DrawWindowBackground: la barra ya pinta su propio fondo redondeado
        self.color_bar.render(painter, QPoint(x, y), QRegion(),
                              QWidget.RenderFlag.DrawChildren)
        painter.end()

    # ============ Limpieza ============
    
    def __del__(self):
        """Limpieza de recursos OpenGL"""
        if hasattr(self, 'gl_initialized') and self.gl_initialized:
            self.cleanup()
    
    def cleanup(self):
        """Limpia todos los recursos OpenGL"""
        try:
            if self.buffers_created:
                self.makeCurrent()
                self.buffer_manager.cleanup()
                self.colormap_manager.cleanup()
                self.doneCurrent()
                self.buffers_created = False
            print("Recursos OpenGL liberados")
        except:
            pass