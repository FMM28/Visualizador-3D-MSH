"""
Ventana principal de la aplicación
"""
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from widgets import OpenGLWidget
from ui import SidePanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador 3D")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()

        # Datos del modelo
        self.original_coords = None
        self.triangle_indices = None
        self.line_indices = None

        # Configurar UI
        self._setup_ui()
        
        # Flag de inicialización
        self.geometry_loaded = False

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Widget OpenGL (sin geometría inicial)
        self.gl_widget = OpenGLWidget()

        # Panel lateral
        self.side_panel = SidePanel(self.gl_widget)
        
        # Añadir widgets al layout
        main_layout.addWidget(self.side_panel)
        main_layout.addWidget(self.gl_widget, 1)
    
    def initialize_geometry(self, coords, triangle_indices, line_indices):
        """Inicializa la geometría del modelo"""
        # Guardar datos originales
        self.original_coords = coords.copy() if isinstance(coords, np.ndarray) else np.array(coords)
        self.triangle_indices = triangle_indices
        self.line_indices = line_indices
        
        # Convertir a listas si es necesario
        coords_list = self.original_coords.tolist()
        tri_list = triangle_indices.tolist() if hasattr(triangle_indices, 'tolist') else triangle_indices
        line_list = line_indices.tolist() if hasattr(line_indices, 'tolist') else line_indices
        
        # Inicializar widget OpenGL
        self.gl_widget.initialize_geometry(coords_list, tri_list, line_list)
        
        # Estado inicial
        self.gl_widget.set_mode("combined")
        
        self.geometry_loaded = True
        return self
        
    def set_data(self, original_coords, displacement_data):
        """Establece los datos de desplazamiento"""
        if not self.geometry_loaded:
            print("Advertencia: Geometría no inicializada. Llame a initialize_geometry() primero.")
            return
        
        self.side_panel.displacements_page.set_data(original_coords, displacement_data)