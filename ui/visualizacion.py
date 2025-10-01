"""
Página de configuración de visualización
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QComboBox, QSlider, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from .styles import get_page_style, BUTTON_STYLE


class VisualizationPage(QWidget):
    def __init__(self, gl_widget):
        super().__init__()
        self.gl_widget = gl_widget
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet(get_page_style() + BUTTON_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título
        title = QLabel("Configuración de Visualización")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        layout.addWidget(title)

        # Modo de visualización
        layout.addWidget(self._create_mode_group())

        # Grosor de línea
        layout.addWidget(self._create_line_width_group())

        # Color de fondo
        layout.addWidget(self._create_appearance_group())

        # Control de cámara
        layout.addWidget(self._create_camera_group())

        layout.addStretch()
    
    def _create_mode_group(self):
        """Crea el grupo de modo de renderizado"""
        mode_group = QGroupBox("Modo de Renderizado")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(8)
        
        mode_label = QLabel("Seleccione el modo de visualización:")
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Sólido", "solid")
        self.mode_combo.addItem("Alámbrico", "wireframe")
        self.mode_combo.addItem("Combinado", "combined")
        self.mode_combo.setCurrentIndex(2)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        return mode_group
    
    def _create_line_width_group(self):
        """Crea el grupo de grosor de líneas"""
        width_group = QGroupBox("Grosor de Líneas")
        width_layout = QVBoxLayout(width_group)
        width_layout.setSpacing(8)

        initial_width = getattr(self.gl_widget, 'line_width', 2.0)
        self.width_label = QLabel(f"Grosor: {initial_width:.1f} px")
        self.width_label.setStyleSheet("font-size: 11px; color: #e0e0e0; font-weight: 600;")
        width_layout.addWidget(self.width_label)

        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 100)
        self.width_slider.setValue(int(initial_width * 10))
        self.width_slider.valueChanged.connect(self._on_line_width_changed)
        width_layout.addWidget(self.width_slider)

        return width_group
    
    def _create_appearance_group(self):
        """Crea el grupo de apariencia"""
        appearance_group = QGroupBox("Apariencia")
        appearance_layout = QVBoxLayout(appearance_group)
        appearance_layout.setSpacing(8)
        
        bg_label = QLabel("Color de fondo:")
        appearance_layout.addWidget(bg_label)

        self.bg_color_combo = QComboBox()
        self.bg_color_combo.addItem("Gris Oscuro", QColor(25, 25, 25))
        self.bg_color_combo.addItem("Blanco", QColor(255, 255, 255))
        self.bg_color_combo.addItem("Negro", QColor(0, 0, 0))
        self.bg_color_combo.addItem("Azul Oscuro", QColor(10, 20, 40))
        self.bg_color_combo.currentIndexChanged.connect(self._on_bg_color_changed)
        appearance_layout.addWidget(self.bg_color_combo)

        return appearance_group
    
    def _create_camera_group(self):
        """Crea el grupo de control de cámara"""
        camera_group = QGroupBox("Control de Cámara")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(8)
        
        reset_btn = QPushButton("Resetear Vista")
        reset_btn.clicked.connect(self.gl_widget.reset_camera)
        camera_layout.addWidget(reset_btn)
        
        return camera_group
    
    # Slots para eventos
    def _on_mode_changed(self, index):
        """Cambia el modo de visualización"""
        mode = self.mode_combo.itemData(index)
        self.gl_widget.set_mode(mode)
    
    def _on_line_width_changed(self, value):
        """Cambia el grosor de las líneas"""
        line_width = value / 10.0
        self.gl_widget.set_line_width(line_width)
        self.width_label.setText(f"Grosor: {line_width:.1f} px")
    
    def _on_bg_color_changed(self, index):
        """Cambia el color de fondo"""
        color = self.bg_color_combo.itemData(index)
        self.gl_widget.set_bg_color(color)