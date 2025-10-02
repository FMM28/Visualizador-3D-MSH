"""
Página de configuración de visualización
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QComboBox, QSlider, QPushButton, QHBoxLayout,
                             QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .styles import get_page_style, BUTTON_STYLE
from .color_picker import ColorPickerDialog

class VisualizationPage(QWidget):
    def __init__(self, gl_widget):
        super().__init__()
        self.gl_widget = gl_widget
        self.solid_color = (50, 50, 50, 255)  # RGBA default para sólido
        self.line_color = (255, 0, 0, 255)  # RGBA default
        self.bg_color = (25, 25, 25, 255)  # RGB default para fondo
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

        # Color de sólido
        layout.addWidget(self._create_solid_color_group())

        # Color de línea
        layout.addWidget(self._create_line_color_group())

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

        initial_width = getattr(self.gl_widget, 'line_width', 1.0)
        self.width_label = QLabel(f"Grosor: {initial_width:.1f} px")
        self.width_label.setStyleSheet("font-size: 11px; color: #e0e0e0; font-weight: 600;")
        width_layout.addWidget(self.width_label)

        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 100)
        self.width_slider.setValue(int(initial_width * 10))
        self.width_slider.valueChanged.connect(self._on_line_width_changed)
        width_layout.addWidget(self.width_slider)

        return width_group
    
    def _create_solid_color_group(self):
        """Crea el grupo de color de sólido"""
        color_group = QGroupBox("Color de Sólido")
        color_layout = QHBoxLayout(color_group)
        color_layout.setSpacing(10)
        
        # Preview del color de sólido
        self.solid_color_preview = QLabel()
        self.solid_color_preview.setFixedSize(40, 40)
        self._update_solid_color_preview()
        color_layout.addWidget(self.solid_color_preview)
        
        # Botón para abrir selector
        solid_color_picker_btn = QPushButton("Seleccionar Color")
        solid_color_picker_btn.clicked.connect(self._open_solid_color_dialog)
        color_layout.addWidget(solid_color_picker_btn, 1)
        
        return color_group
    
    def _create_line_color_group(self):
        """Crea el grupo de color de líneas"""
        color_group = QGroupBox("Color de Líneas")
        color_layout = QHBoxLayout(color_group)
        color_layout.setSpacing(10)
        
        # Preview del color
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(40, 40)
        self._update_color_preview()
        color_layout.addWidget(self.color_preview)
        
        # Botón para abrir selector
        color_picker_btn = QPushButton("Seleccionar Color")
        color_picker_btn.clicked.connect(self._open_color_dialog)
        color_layout.addWidget(color_picker_btn, 1)
        
        return color_group
    
    def _create_appearance_group(self):
        """Crea el grupo de apariencia"""
        appearance_group = QGroupBox("Color de Fondo")
        appearance_layout = QHBoxLayout(appearance_group)
        appearance_layout.setSpacing(10)
        
        # Preview del color de fondo
        self.bg_color_preview = QLabel()
        self.bg_color_preview.setFixedSize(40, 40)
        self._update_bg_color_preview()
        appearance_layout.addWidget(self.bg_color_preview)
        
        # Botón para abrir selector
        bg_color_picker_btn = QPushButton("Seleccionar Color")
        bg_color_picker_btn.clicked.connect(self._open_bg_color_dialog)
        appearance_layout.addWidget(bg_color_picker_btn, 1)

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
    
    def _open_solid_color_dialog(self):
        """Abre el diálogo de selección de color de sólido"""
        dialog = ColorPickerDialog(self.solid_color, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.solid_color = dialog.get_color()
            self._update_solid_color_preview()
            # Normalizar color para OpenGL (0-255 -> 0.0-1.0)
            normalized_color = tuple(v / 255.0 for v in self.solid_color)
            self.gl_widget.set_solid_color(normalized_color)
    
    def _update_solid_color_preview(self):
        """Actualiza la vista previa del color de sólido"""
        r, g, b, a = self.solid_color
        self.solid_color_preview.setStyleSheet(
            f"background-color: rgba({r}, {g}, {b}, {a});"
            f"border: 2px solid #555; border-radius: 4px;"
        )
    
    def _open_color_dialog(self):
        """Abre el diálogo de selección de color"""
        dialog = ColorPickerDialog(self.line_color, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.line_color = dialog.get_color()
            self._update_color_preview()
            # Normalizar color
            normalized_color = tuple(v / 255.0 for v in self.line_color)
            self.gl_widget.set_line_color(normalized_color)
    
    def _update_color_preview(self):
        """Actualiza la vista previa del color"""
        r, g, b, a = self.line_color
        self.color_preview.setStyleSheet(
            f"background-color: rgba({r}, {g}, {b}, {a});"
            f"border: 2px solid #555; border-radius: 4px;"
        )
    
    def _open_bg_color_dialog(self):
        """Abre el diálogo de selección de color de fondo"""
        dialog = ColorPickerDialog(self.bg_color, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.bg_color = dialog.get_color()
            self._update_bg_color_preview()
            # Normalizar solo RGB, ignorar alpha
            r, g, b, a = self.bg_color
            normalized_color = (r / 255.0, g / 255.0, b / 255.0)
            self.gl_widget.set_bg_color(normalized_color)
    
    def _update_bg_color_preview(self):
        """Actualiza la vista previa del color de fondo"""
        r, g, b, a = self.bg_color
        self.bg_color_preview.setStyleSheet(
            f"background-color: rgba({r}, {g}, {b}, {a});"
            f"border: 2px solid #555; border-radius: 4px;"
        )
    
    def _on_bg_color_changed(self, index):
        """Cambia el color de fondo"""
        color = self.bg_color_combo.itemData(index)
        self.gl_widget.set_bg_color(color)