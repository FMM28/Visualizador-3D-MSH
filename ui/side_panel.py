"""
Panel lateral con pestañas y barra de iconos
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QToolButton,
                             QStackedWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from .styles import SIDE_PANEL_STYLE, ICON_BAR_STYLE, STACKED_WIDGET_STYLE
from .visualizacion import VisualizationPage
from .desplazamientos import DisplacementsPage
from .paleta import PaletaPage
from .archivo import ArchivePage

class SidePanel(QWidget):
    def __init__(self, gl_widget):
        super().__init__()
        self.gl_widget = gl_widget
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del panel lateral"""
        self.setFixedWidth(320)
        self.setStyleSheet(SIDE_PANEL_STYLE)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de iconos lateral
        self.icon_bar = self._create_icon_bar()
        layout.addWidget(self.icon_bar)

        # Área de contenido con páginas
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(STACKED_WIDGET_STYLE)
        layout.addWidget(self.content_stack)

        # Crear y añadir páginas
        self.archive_page = ArchivePage()
        self.visualization_page = VisualizationPage(self.gl_widget)
        self.displacements_page = DisplacementsPage(self.gl_widget)
        self.palette_page = PaletaPage(self.gl_widget)
        
        self.content_stack.addWidget(self.archive_page)
        self.content_stack.addWidget(self.visualization_page)
        self.content_stack.addWidget(self.displacements_page)
        self.content_stack.addWidget(self.palette_page)
        
        self._switch_page(0)
    
    def _create_icon_bar(self):
        """Crea la barra lateral de iconos"""
        icon_bar = QWidget()
        icon_bar.setFixedWidth(60)
        icon_bar.setStyleSheet(ICON_BAR_STYLE)
        
        icon_layout = QVBoxLayout(icon_bar)
        icon_layout.setContentsMargins(5, 15, 5, 15)
        icon_layout.setSpacing(5)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Botón de Archivo
        self.arch_btn = self._create_icon_button(
            "icons/archivo.svg",
            "Archivo",
            lambda: self._switch_page(0)
        )
        icon_layout.addWidget(self.arch_btn)
        
        # Botón de Visualización
        self.vis_btn = self._create_icon_button(
            "icons/camara.svg",
            "Visualización",
            lambda: self._switch_page(1)
        )
        self.vis_btn.setChecked(True)
        icon_layout.addWidget(self.vis_btn)

        # Botón de Desplazamientos
        self.disp_btn = self._create_icon_button(
            "icons/desp.svg",
            "Desplazamientos",
            lambda: self._switch_page(2)
        )
        icon_layout.addWidget(self.disp_btn)
        
        # Botón de Paleta
        self.pal_btn = self._create_icon_button(
            "icons/paleta.svg",
            "Paleta",
            lambda: self._switch_page(3)
        )
        icon_layout.addWidget(self.pal_btn)

        icon_layout.addStretch()

        return icon_bar
    
    def _create_icon_button(self, icon_path, tooltip, callback):
        """Crea un botón de icono configurado"""
        btn = QToolButton()
        btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setFixedSize(50, 50)
        btn.setIconSize(QSize(24, 24))
        btn.clicked.connect(callback)
        return btn
    
    def _switch_page(self, page_index):
        """Cambia entre páginas del stack"""
        # Desmarcar todos los botones
        self.arch_btn.setChecked(False)
        self.vis_btn.setChecked(False)
        self.disp_btn.setChecked(False)
        self.pal_btn.setChecked(False)
        
        # Marcar el botón correspondiente
        if page_index == 0:
            self.arch_btn.setChecked(True)
        elif page_index == 1:
            self.vis_btn.setChecked(True)
        elif page_index == 2:
            self.disp_btn.setChecked(True)
        elif page_index == 3:
            self.pal_btn.setChecked(True)
        
        # Cambiar de página
        self.content_stack.setCurrentIndex(page_index)
    
    # Métodos públicos para acceder a las páginas
    def get_visualization_page(self):
        """Retorna la página de visualización"""
        return self.visualization_page
    
    def get_displacements_page(self):
        """Retorna la página de desplazamientos"""
        return self.displacements_page