"""
Visor de imágenes a pantalla completa con zoom y desplazamiento
"""
from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QPushButton,
)

from .styles import CLOSE_BUTTON_STYLE, HUD_STYLE


class FullScreenImageViewer(QGraphicsView):
    """
    Muestra una imagen a pantalla completa.

    Controles:
        Rueda del ratón      zoom centrado en el cursor
        Arrastrar            mover la imagen
        Doble clic           alternar entre 100 % y ajustar a pantalla
        0 / 1                ajustar a pantalla / 100 %
        + / -                acercar / alejar
        Esc, F, F11          salir
    """

    ZOOM_STEP = 1.25
    MIN_ZOOM = 0.05
    MAX_ZOOM = 32.0
    MARGIN = 16
    HINT_TIMEOUT_MS = 5000

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Imagen renderizada")

        image = pixmap.copy()
        image.setDevicePixelRatio(1.0)
        self._original = image
        self._image_size = image.size()

        self._reduced = None
        self._reduced_size = None

        self._scene = QGraphicsScene(self)
        self._item = QGraphicsPixmapItem(image)
        self._scene.addItem(self._item)
        self._scene.setSceneRect(QRectF(image.rect()))
        self.setScene(self._scene)

        # Aspecto y navegación
        self.setBackgroundBrush(QColor(12, 12, 12))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        self._fit_mode = True
        self._create_overlay()

    # ============ Overlay ============

    def _create_overlay(self):
        """Crea las etiquetas de información y el botón de cerrar"""
        self._info_label = QLabel(self)
        self._info_label.setStyleSheet(HUD_STYLE)
        self._info_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._hint_label = QLabel(
            "Rueda: zoom  ·  Arrastrar: mover  ·  Doble clic: 100 % / ajustar  ·  "
            "0: ajustar  ·  1: 100 %  ·  Esc: salir", self)
        self._hint_label.setStyleSheet(HUD_STYLE)
        self._hint_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._hint_label.adjustSize()

        self._close_button = QPushButton("✕  Cerrar", self)
        self._close_button.setStyleSheet(CLOSE_BUTTON_STYLE)
        self._close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._close_button.clicked.connect(self.close)
        self._close_button.adjustSize()

        QTimer.singleShot(self.HINT_TIMEOUT_MS, self._hint_label.hide)

    def _place_overlay(self):
        """Coloca el overlay en las esquinas de la pantalla"""
        m = self.MARGIN
        self._info_label.move(m, m)
        self._close_button.move(self.width() - self._close_button.width() - m, m)
        self._hint_label.move((self.width() - self._hint_label.width()) // 2,
                              self.height() - self._hint_label.height() - m)

    def _update_info(self):
        w, h = self._image_size.width(), self._image_size.height()
        self._info_label.setText(f"{w} × {h} px  ·  Zoom {self.zoom_percent():.0f} %")
        self._info_label.adjustSize()

    # ============ Zoom ============

    def _one_to_one_scale(self):
        """Escala con la que 1 píxel de la imagen ocupa 1 píxel físico de la pantalla"""
        return 1.0 / self.devicePixelRatioF()

    def _current_scale(self):
        return self.transform().m11()

    def zoom_percent(self):
        return self._current_scale() / self._one_to_one_scale() * 100.0

    def _set_scale(self, scale):
        factor = scale / self._current_scale()
        self.scale(factor, factor)
        self._update_display_pixmap()
        self._update_info()

    def _update_display_pixmap(self):
        """
        Por debajo del 100 % muestra una copia reducida con el filtro de calidad de Qt
        (promedia los píxeles, así no aparecen moiré ni líneas que desaparecen).
        Por encima del 100 % muestra el original con píxeles nítidos.
        """
        # Píxeles físicos de pantalla por píxel de imagen
        density = self._current_scale() * self.devicePixelRatioF()

        if density < 0.999:
            w = max(1, round(self._image_size.width() * density))
            h = max(1, round(self._image_size.height() * density))
            if self._reduced_size != (w, h):
                self._reduced = self._original.scaled(
                    w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                self._reduced_size = (w, h)
            self._item.setPixmap(self._reduced)
            self._item.setScale(self._image_size.width() / w)
            smooth = True
        else:
            self._item.setPixmap(self._original)
            self._item.setScale(1.0)
            smooth = density < 1.001   # Exactamente 100 %: da igual; >100 %: nítido

        self._item.setTransformationMode(
            Qt.TransformationMode.SmoothTransformation if smooth
            else Qt.TransformationMode.FastTransformation)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, smooth)

    def fit_to_screen(self):
        """Ajusta la imagen completa a la pantalla (sin ampliar por encima del 100 %)"""
        self._fit_mode = True
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self._current_scale() > self._one_to_one_scale():
            self._set_scale(self._one_to_one_scale())
        self.centerOn(self._scene.sceneRect().center())
        self._update_display_pixmap()
        self._update_info()

    def actual_size(self):
        """Muestra la imagen al 100 % (centrado en el cursor si está sobre la imagen)"""
        self._fit_mode = False
        self._set_scale(self._one_to_one_scale())

    def zoom_by(self, factor):
        one = self._one_to_one_scale()
        target = self._current_scale() * factor
        target = min(max(target, one * self.MIN_ZOOM), one * self.MAX_ZOOM)
        self._fit_mode = False
        self._set_scale(target)

    # ============ Eventos ============

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_to_screen()
        self._place_overlay()
        self.setFocus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit_mode:
            self.fit_to_screen()
        self._place_overlay()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta:
            self.zoom_by(self.ZOOM_STEP if delta > 0 else 1 / self.ZOOM_STEP)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._fit_mode or self.zoom_percent() < 99.5:
                self.actual_size()
            else:
                self.fit_to_screen()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F, Qt.Key.Key_F11):
            self.close()
        elif key == Qt.Key.Key_0:
            self.fit_to_screen()
        elif key == Qt.Key.Key_1:
            self.actual_size()
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_by(self.ZOOM_STEP)
        elif key == Qt.Key.Key_Minus:
            self.zoom_by(1 / self.ZOOM_STEP)
        else:
            super().keyPressEvent(event)