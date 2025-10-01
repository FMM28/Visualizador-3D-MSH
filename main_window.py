"""
Ventana principal de la aplicación
"""
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from widgets import OpenGLWidget
from ui import SidePanel

class MainWindow(QMainWindow):
    def __init__(self, coords, triangle_indices, line_indices, desplazamientos=None):
        super().__init__()
        self.setWindowTitle("Visualizador 3D")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()

        # Datos del modelo
        self.original_coords = coords.copy() if isinstance(coords, np.ndarray) else np.array(coords)
        self.current_coords = self.original_coords.copy()
        self.disp_array = desplazamientos

        # Configurar UI
        self._setup_ui(triangle_indices, line_indices)
        self._connect_signals()
        
        # Estado inicial
        self._initialize_state()

    def _setup_ui(self, triangle_indices, line_indices):
        """Configura la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Widget OpenGL
        self.gl_widget = OpenGLWidget(
            self.current_coords.tolist(),
            triangle_indices.tolist() if hasattr(triangle_indices, 'tolist') else triangle_indices,
            line_indices.tolist() if hasattr(line_indices, 'tolist') else line_indices
        )

        # Panel lateral
        has_displacements = self.disp_array is not None
        self.side_panel = SidePanel(self.gl_widget, has_displacements)
        
        # Añadir widgets al layout
        main_layout.addWidget(self.side_panel)
        main_layout.addWidget(self.gl_widget, 1)
    
    def _connect_signals(self):
        """Conecta las señales de los componentes"""
        disp_page = self.side_panel.get_displacements_page()
        disp_page.displacements_toggled.connect(self._on_displacements_toggled)
        disp_page.factor_changed.connect(self._on_factor_changed)
    
    def _initialize_state(self):
        """Inicializa el estado de la aplicación"""
        self.gl_widget.set_mode("combined")
        
        # Inicializar desplazamientos si existen
        disp_page = self.side_panel.get_displacements_page()
        if disp_page.is_checked():
            self._update_displacements(disp_page.get_factor())

    # --- Métodos de control de desplazamientos ---
    
    def _on_displacements_toggled(self, state):
        """Maneja la activación/desactivación de desplazamientos"""
        if state == Qt.CheckState.Checked.value and self.disp_array is not None:
            disp_page = self.side_panel.get_displacements_page()
            self._update_displacements(disp_page.get_factor())
        else:
            self._reset_to_original()
    
    def _on_factor_changed(self, value):
        """Maneja el cambio del factor de amplificación"""
        disp_page = self.side_panel.get_displacements_page()
        if disp_page.is_checked() and self.disp_array is not None:
            self._update_displacements(value)
    
    def _update_displacements(self, factor):
        """Actualiza las coordenadas con desplazamientos amplificados"""
        if self.disp_array is None:
            return
        
        self.current_coords = self.original_coords + factor * self.disp_array
        self.gl_widget.update_coords(self.current_coords)
    
    def _reset_to_original(self):
        """Restaura las coordenadas originales sin desplazamientos"""
        self.current_coords = self.original_coords.copy()
        self.gl_widget.update_coords(self.current_coords.tolist())