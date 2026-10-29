"""
Clase base para páginas que muestran gradientes en el widget OpenGL.
"""
import numpy as np
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QLabel, QWidget

from .styles import RANGE_LABEL_STYLE


class GradientPage(QWidget):
    """Base común: helpers de UI + gestión exclusiva del gradiente."""

    # Se emite cuando esta página toma el control del gradiente
    gradient_activated = pyqtSignal()

    def __init__(self, gl_widget):
        super().__init__()
        self.gl_widget = gl_widget
        self.gradient_checkbox = None
        self.range_label = None


    def _create_title(self, text):
        """Crea el título de la página"""
        title = QLabel(text)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        return title

    def _create_separator(self):
        """Crea un separador visual horizontal"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #404040; max-height: 1px;")
        return separator

    def _create_label(self, text):
        """Crea un label con estilo predeterminado"""
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #b0b0b0; padding-top: 4px;")
        return label

    def _create_range_label(self):
        """Crea el label que muestra el rango de valores del gradiente"""
        label = QLabel("Rango: --")
        label.setStyleSheet(RANGE_LABEL_STYLE)
        label.setWordWrap(True)
        return label

    def is_gradient_active(self):
        """Indica si el gradiente de esta página está marcado"""
        return self.gradient_checkbox is not None and self.gradient_checkbox.isChecked()

    def _apply_gradient_values(self, values, title=""):
        """
        Envía valores nodales al widget GL, activa el gradiente y actualiza el rango.
        `title` se muestra en la barra de colores del área de render.
        """
        if self.gl_widget is None:
            return
        values = np.asarray(values, dtype=np.float32)
        self.gl_widget.set_colorbar_title(title)
        self.gl_widget.set_node_values(values, auto_range=True)
        self.gl_widget.enable_gradient(True)
        self._set_range_text(float(np.min(values)), float(np.max(values)))

    def _disable_gl_gradient(self):
        """Apaga el gradiente en el widget GL y limpia el rango"""
        if self.gl_widget is not None:
            self.gl_widget.enable_gradient(False)
        self._clear_range()

    def _set_range_text(self, vmin, vmax):
        if self.range_label is not None:
            self.range_label.setText(f"Rango: {vmin:.6g} a {vmax:.6g}")

    def _clear_range(self, text="Rango: --"):
        if self.range_label is not None:
            self.range_label.setText(text)

    def _uncheck_gradient_silently(self):
        """Desmarca el checkbox de gradiente sin disparar sus slots"""
        if self.gradient_checkbox is None:
            return
        self.gradient_checkbox.blockSignals(True)
        self.gradient_checkbox.setChecked(False)
        self.gradient_checkbox.blockSignals(False)

    def deactivate_gradient(self):
        """
        Desactiva el gradiente de esta página porque otra tomó el control.
        No toca el widget GL: la otra página es la que está mostrando su gradiente.
        """
        if not self.is_gradient_active():
            return
        self._uncheck_gradient_silently()
        self._clear_range()
        self._on_gradient_released()

    def _on_gradient_released(self):
        """Hook para que las subclases limpien su UI al perder el gradiente"""
        pass