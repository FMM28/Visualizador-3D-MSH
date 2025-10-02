"""
Página de configuración de paleta de colores
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QButtonGroup,
                             QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QLinearGradient, QColor, QPainter, QPen
from .styles import (PALETTE_PAGE_STYLE, PALETTE_BUTTON_STYLE, PALETTE_NAME_LABEL_STYLE)

class ColorPreviewWidget(QWidget):
    """Widget que muestra una vista previa de la paleta de colores"""
    
    def __init__(self, palette_name, colormap_manager, parent=None):
        super().__init__(parent)
        self.palette_name = palette_name
        self.colormap_manager = colormap_manager
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)
        
    def paintEvent(self, event):
        """Dibuja el gradiente de la paleta"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Crear gradiente lineal
        gradient = QLinearGradient(0, 0, self.width(), 0)
        
        # Obtener colores de la paleta
        colors = self.colormap_manager.get_palette_colors(self.palette_name)
        
        if colors:
            n_stops = len(colors)
            for i, color in enumerate(colors):
                position = i / (n_stops - 1) if n_stops > 1 else 0
                gradient.setColorAt(position, QColor.fromRgbF(*color))
        
        # Dibujar rectángulo con gradiente
        painter.fillRect(self.rect(), gradient)
        
        # Borde
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))


class PaletaPage(QWidget):
    """Página para selección de paleta de colores de gradientes"""
    
    palette_changed = pyqtSignal(str)
    
    def __init__(self, gl_widget):
        super().__init__()
        self.gl_widget = gl_widget
        self.colormap_manager = gl_widget.colormap_manager if gl_widget else None
        self.current_palette = 'viridis'
        self.palette_buttons = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet(PALETTE_PAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        layout.addWidget(self._create_title())
        layout.addWidget(self._create_palette_selector())
        layout.addStretch()
    
    def _create_title(self):
        """Crea el título de la página"""
        title = QLabel("Paletas de Colores")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        return title
    
    def _create_palette_selector(self):
        """Crea el selector de paletas con scroll"""
        group = QGroupBox("Paletas Disponibles")
        group_layout = QVBoxLayout(group)
        
        # Área con scroll para las paletas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget contenedor de paletas
        palette_container = QWidget()
        palette_layout = QVBoxLayout(palette_container)
        palette_layout.setSpacing(8)
        palette_layout.setContentsMargins(5, 5, 5, 5)
        
        # Grupo de botones para selección única
        self.button_group = QButtonGroup(self)
        
        # Obtener paletas disponibles del gl_widget
        available_palettes = self._get_available_palettes()
        
        # Crear botones para cada paleta
        for palette_name in available_palettes:
            palette_widget = self._create_palette_widget(palette_name)
            palette_layout.addWidget(palette_widget)
            
            # Marcar la paleta actual
            if palette_name == self.current_palette:
                self.palette_buttons[palette_name].setChecked(True)
        
        scroll.setWidget(palette_container)
        group_layout.addWidget(scroll)
        
        return group
    
    def _create_palette_widget(self, palette_name):
        """Crea un widget para mostrar una paleta"""
        # Botón checkeable
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setMinimumHeight(50)
        btn.setStyleSheet(PALETTE_BUTTON_STYLE)
        
        btn.clicked.connect(lambda: self._on_palette_selected(palette_name))
        self.button_group.addButton(btn)
        self.palette_buttons[palette_name] = btn
        
        # Layout interno del botón
        btn_layout = QVBoxLayout(btn)
        btn_layout.setSpacing(4)
        btn_layout.setContentsMargins(8, 6, 8, 6)
        
        # Nombre de la paleta
        name_label = QLabel(palette_name.capitalize())
        name_label.setStyleSheet(PALETTE_NAME_LABEL_STYLE)
        btn_layout.addWidget(name_label)
        
        # Vista previa del gradiente
        preview = ColorPreviewWidget(palette_name, self.colormap_manager)
        btn_layout.addWidget(preview)
        
        return btn
    
    def _get_available_palettes(self):
        """Obtiene la lista de paletas disponibles del gl_widget"""
        if self.gl_widget and hasattr(self.gl_widget, 'get_available_palettes'):
            return self.gl_widget.get_available_palettes()
        return ['viridis']  # Fallback por defecto
    
    def _on_palette_selected(self, palette_name):
        """Maneja la selección de una paleta"""
        self.current_palette = palette_name
        
        # Actualizar GL widget
        if self.gl_widget:
            self.gl_widget.set_color_palette(palette_name)
        
        self.palette_changed.emit(palette_name)