"""
Widget OpenGL
"""
import numpy as np
from OpenGL.GL import *
from PyQt6 import sip
from PyQt6.QtCore import QEasingCurve, QPoint, Qt, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QRegion, QSurfaceFormat
from PyQt6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QWidget

from utils import Matrix44

from .modules import (
    BufferManager,
    Camera,
    ColorBar,
    ColormapManager,
    Renderer,
    ShaderManager,
    ViewControls,
)
from .modules.cameraController import (
    PITCH_LIMIT,
    VIEWS,
)


class OpenGLWidget(QOpenGLWidget):
    """Widget OpenGL para visualización de modelos 3D"""

    camera_changed = pyqtSignal()

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

        # Control de vistas (ViewCube + flechas)
        self.orbit_step_deg = 15
        self._anim = None
        self._goal = None
        self._view_controls_enabled = True
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Barra de colores superpuesta
        self.color_bar = ColorBar(self)
        self.color_bar.set_colors(
            self.colormap_manager.get_palette_colors(self.colormap_manager.current_palette)
        )

        self.view_controls = ViewControls(self)

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

        self._update_view_controls_visibility()
        self.camera_changed.emit()

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
        self.view_controls.reposition()

    # ============ Control de vista (ViewCube, flechas y atajos) ============

    def _update_view_controls_visibility(self):
        """Muestra los controles si hay modelo y el usuario no los ocultó"""
        visible = self._view_controls_enabled and self.camera is not None
        self.view_controls.setVisible(visible)
        if visible:
            self.view_controls.reposition()

    def set_view_controls_visible(self, visible):
        """Muestra/oculta los controles de vista (los atajos siguen activos)"""
        self._view_controls_enabled = bool(visible)
        self._update_view_controls_visibility()

    def set_orbit_step(self, degrees):
        """Establece el paso (en grados) de las flechas y atajos"""
        self.orbit_step_deg = float(degrees)

    def _apply_angles(self, ry, rx):
        """Aplica ángulos a la cámara y refresca"""
        if not self.camera:
            return
        cam = self.camera
        cam.rotation_y = (ry + np.pi) % (2 * np.pi) - np.pi
        cam.rotation_x = float(np.clip(rx, -PITCH_LIMIT, PITCH_LIMIT))
        self.update()
        self.camera_changed.emit()

    def _base_angles(self):
        """Destino de la animación en curso, o la orientación actual.
        Así pulsaciones rápidas se acumulan en lugar de pisarse."""
        if self._anim and self._anim.state() == QVariantAnimation.State.Running:
            return self._goal
        return self.camera.rotation_y, self.camera.rotation_x

    def _stop_animation(self):
        if self._anim:
            self._anim.stop()
            self._anim = None

    def _animate_to(self, ry, rx, ms=250):
        """Anima la cámara hasta (ry, rx) por el camino más corto"""
        if not self.camera:
            return
        rx = float(np.clip(rx, -PITCH_LIMIT, PITCH_LIMIT))
        ry0, rx0 = self.camera.rotation_y, self.camera.rotation_x
        dy = (ry - ry0 + np.pi) % (2 * np.pi) - np.pi
        self._goal = (ry0 + dy, rx)

        self._stop_animation()
        if ms <= 0:
            self._apply_angles(*self._goal)
            return

        anim = QVariantAnimation(self)
        anim.setDuration(ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(
            lambda k: self._apply_angles(ry0 + dy * k, rx0 + (rx - rx0) * k))
        anim.start()
        self._anim = anim

    def go_to_view(self, name):
        """Va a una vista estándar: front, back, left, right, top, bottom, iso"""
        self._animate_to(*VIEWS[name])

    def go_to_direction(self, direction):
        """Orienta la cámara para mirar desde 'direction' (vector en coordenadas mundo
        hacia el observador). La usa el ViewCube al pulsar una arista o una esquina."""
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        self._animate_to(np.arctan2(d[2], d[0]), np.arcsin(np.clip(d[1], -1.0, 1.0)))

    def orbit_step(self, yaw_dir=0, pitch_dir=0, step_deg=None):
        """Gira un paso, ajustando antes a la cuadrícula del paso:
        desde 83° con paso de 90° se llega a 90° (o 180°), no a 173°."""
        if not self.camera:
            return
        step = np.radians(step_deg or self.orbit_step_deg)
        ry, rx = self._base_angles()
        if yaw_dir:
            ry = round(ry / step) * step + yaw_dir * step
        if pitch_dir:
            rx = round(rx / step) * step + pitch_dir * step
        self._animate_to(ry, rx)

    # ============ Eventos de Teclado ============

    def keyPressEvent(self, e):
        """Atajos del teclado numérico (o fila superior):
            5 → restablecer cámara        8 / 2 → vista superior / inferior
            4 / 6 → girar 90° izq. / der. 7 / 9 → girar 15° izq. / der.
            1 / 3 → girar 15° arriba / abajo  0 → isométrica   . → vista trasera
            + / - → acercar / alejar          W/A/S/D → paneo (arriba/izq./abajo/der.)
        Las flechas giran con el paso configurado en el sidebar."""
        if not self.camera:
            return super().keyPressEvent(e)

        K = Qt.Key
        actions = {
            K.Key_5: self.reset_camera,
            K.Key_8: lambda: self.go_to_view("top"),
            K.Key_2: lambda: self.go_to_view("bottom"),
            K.Key_4: lambda: self.orbit_step(yaw_dir=-1, step_deg=90),
            K.Key_6: lambda: self.orbit_step(yaw_dir=1, step_deg=90),
            K.Key_7: lambda: self.orbit_step(yaw_dir=-1, step_deg=15),
            K.Key_9: lambda: self.orbit_step(yaw_dir=1, step_deg=15),
            K.Key_1: lambda: self.orbit_step(pitch_dir=-1, step_deg=15),
            K.Key_3: lambda: self.orbit_step(pitch_dir=1, step_deg=15),
            K.Key_0: lambda: self.go_to_view("iso"),
            K.Key_Period: lambda: self.go_to_view("back"),
            K.Key_Plus:  lambda: self.zoom_step(1),
            K.Key_Equal: lambda: self.zoom_step(1),    # "+" sin Shift en teclados US
            K.Key_Minus: lambda: self.zoom_step(-1),
            # Paneo: mueve la cámara (el modelo se desplaza en sentido contrario)
            K.Key_W: lambda: self.pan_step(0, 1),
            K.Key_S: lambda: self.pan_step(0, -1),
            K.Key_A: lambda: self.pan_step(-1, 0),
            K.Key_D: lambda: self.pan_step(1, 0),
            # Flechas: paso del sidebar
            K.Key_Left:  lambda: self.orbit_step(yaw_dir=-1),
            K.Key_Right: lambda: self.orbit_step(yaw_dir=1),
            K.Key_Up:    lambda: self.orbit_step(pitch_dir=-1),
            K.Key_Down:  lambda: self.orbit_step(pitch_dir=1),
            K.Key_Home:  self.reset_camera,
        }

        key = e.key()
        # Algunas distribuciones (p. ej. España) dan "," en el punto del teclado numérico
        if key == K.Key_Comma and e.modifiers() & Qt.KeyboardModifier.KeypadModifier:
            key = K.Key_Period

        action = actions.get(key)
        if action:
            action()
            e.accept()
        else:
            super().keyPressEvent(e)

    # ============ Eventos de Mouse ============

    def mousePressEvent(self, event):
        """Maneja el evento de presión del mouse"""
        self.setFocus()              # para recibir las teclas
        self._stop_animation()       # un arrastre cancela la animación
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
            self.camera_changed.emit()
        elif buttons & Qt.MouseButton.RightButton:
            self.camera.pan(dx, dy)
            self.update()

    def wheelEvent(self, event):
        """Maneja el evento de la rueda del mouse"""
        self.zoom_step(event.angleDelta().y() / 120)

    PAN_KEY_STEP = 0.05   # fracción de la distancia de la cámara por pulsación de W/A/S/D

    def pan_step(self, right, up):
        """Desplaza la cámara un paso a la derecha (right=1) / izquierda (-1)
        y arriba (up=1) / abajo (-1). Mantener la tecla repite el paso."""
        if not self.camera:
            return
        # Camera.pan() trabaja en píxeles de arrastre: su eje "right" apunta a la
        # izquierda de la pantalla (arrastre tipo "agarrar"), por eso el signo de x
        px = self.PAN_KEY_STEP / self.camera.pan_speed
        self.camera.pan(-right * px, up * px)
        self.update()

    def zoom_step(self, amount):
        """Acerca (amount > 0) o aleja (amount < 0); 1 equivale a un paso de la rueda"""
        if self.camera and amount:
            self.camera.zoom(amount)
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

    def set_line_color(self, color):
        """Establece el color de línea"""
        self.renderer.set_line_color(color)
        self.update()

    def set_solid_color(self, color):
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
            self._stop_animation()
            self.camera.reset()
            self.update()
            self.camera_changed.emit()

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
        sin modificar el widget visible. Los controles de vista (ViewCube y flechas)
        son widgets hijos y nunca aparecen en la imagen.
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