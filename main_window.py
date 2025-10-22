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
        
        self.reset_camera_on_next_load = True

        # Configurar UI
        self._setup_ui()

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
        
        # Conectar señales
        self.side_panel.archive_page.modelo_cargado.connect(self._on_modelo_cargado)
        self.side_panel.archive_page.carpeta_cambiada.connect(self._on_carpeta_cambiada)
        
        # Añadir widgets al layout
        main_layout.addWidget(self.side_panel)
        main_layout.addWidget(self.gl_widget, 1)
    
    def _on_carpeta_cambiada(self):
        """Callback cuando se cambia de carpeta"""
        self.reset_camera_on_next_load = True
    
    def _on_modelo_cargado(self, datos_modelo):
        """Callback cuando se carga un modelo desde ArchivePage"""
        coords = datos_modelo['coords']
        triangle_indices = datos_modelo['triangle_indices']
        line_indices = datos_modelo['line_indices']
        desplazamientos = datos_modelo['desplazamientos']
        
        # Convertir coords a numpy array si no lo es
        if not isinstance(coords, np.ndarray):
            coords = np.array(coords)
        
        # Convertir índices a listas para OpenGL
        tri_list = triangle_indices.tolist() if hasattr(triangle_indices, 'tolist') else triangle_indices
        line_list = line_indices.tolist() if hasattr(line_indices, 'tolist') else line_indices
        
        # Guardar el modo actual antes de inicializar
        current_mode = self.gl_widget.current_mode
        
        # Inicializar widget OpenGL con flag de reset de cámara
        self.gl_widget.initialize_geometry(
            coords.tolist(), 
            tri_list, 
            line_list,
            reset_camera=self.reset_camera_on_next_load
        )
        
        # Después del primer modelo de la carpeta, no resetear más
        self.reset_camera_on_next_load = False
        
        # Restaurar el modo de visualización
        self.gl_widget.set_mode(current_mode)
        
        # Establecer datos de desplazamientos
        self.side_panel.displacements_page.set_data(coords, desplazamientos)