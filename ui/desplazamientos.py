"""
Página de configuración de desplazamientos
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QSlider, QCheckBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .styles import get_page_style


class DisplacementsPage(QWidget):
    # Señales para comunicarse con la ventana principal
    displacements_toggled = pyqtSignal(int)
    factor_changed = pyqtSignal(int)
    
    def __init__(self, has_displacements=False):
        super().__init__()
        self.has_displacements = has_displacements
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet(get_page_style())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título
        title = QLabel("Configuración de Desplazamientos")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        layout.addWidget(title)

        # Control de desplazamientos
        layout.addWidget(self._create_displacement_group())

        layout.addStretch()
    
    def _create_displacement_group(self):
        """Crea el grupo de control de deformación"""
        disp_group = QGroupBox("Control de Deformación")
        disp_layout = QVBoxLayout(disp_group)
        disp_layout.setSpacing(10)

        # Checkbox para activar/desactivar
        self.disp_checkbox = QCheckBox("Activar deformaciones")
        self.disp_checkbox.setEnabled(self.has_displacements)
        self.disp_checkbox.stateChanged.connect(self._on_toggle_displacements)
        disp_layout.addWidget(self.disp_checkbox)

        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #404040; max-height: 1px;")
        disp_layout.addWidget(separator)

        # Label del factor
        amp_label = QLabel("Factor de amplificación:")
        amp_label.setStyleSheet("font-size: 11px; color: #b0b0b0; padding-top: 4px;")
        disp_layout.addWidget(amp_label)
        
        # Slider para el factor
        self.factor_slider = QSlider(Qt.Orientation.Horizontal)
        self.factor_slider.setRange(0, 1000)
        self.factor_slider.setValue(100)
        self.factor_slider.setEnabled(False)
        self.factor_slider.valueChanged.connect(self._on_factor_changed)
        disp_layout.addWidget(self.factor_slider)

        # Label que muestra el valor actual
        self.factor_label = QLabel(f"Factor: {self.factor_slider.value()}")
        self.factor_label.setStyleSheet("font-size: 11px; color: #e0e0e0; font-weight: 600; padding: 4px;")
        disp_layout.addWidget(self.factor_label)

        return disp_group
    
    # Slots para eventos
    def _on_toggle_displacements(self, state):
        """Maneja el cambio de estado del checkbox"""
        self.factor_slider.setEnabled(state == Qt.CheckState.Checked.value)
        self.displacements_toggled.emit(state)
    
    def _on_factor_changed(self, value):
        """Maneja el cambio del factor de amplificación"""
        self.factor_label.setText(f"Factor: {value}")
        self.factor_changed.emit(value)
    
    # Métodos públicos
    def is_checked(self):
        """Retorna si el checkbox está marcado"""
        return self.disp_checkbox.isChecked()
    
    def get_factor(self):
        """Retorna el valor actual del factor"""
        return self.factor_slider.value()