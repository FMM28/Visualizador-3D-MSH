import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QGroupBox, QLabel,
                             QComboBox, QSlider, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from msh import Lector
from OpenGLWidget import OpenGLWidget
from malla import filtrar_elementos_visibles, mapear_desplazamientos

class MainWindow(QMainWindow):
    def __init__(self, coords, elements, lines, desplazamientos=None):
        super().__init__()
        self.setWindowTitle("Visualizador 3D")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()

        self.original_coords = coords.copy() if isinstance(coords, np.ndarray) else np.array(coords)
        
        self.disp_array = desplazamientos
        
        if self.disp_array is not None:
            print(f"Desplazamientos configurados para {len(self.disp_array)} nodos visibles")
        else:
            print("No hay desplazamientos disponibles.")

        self.current_coords = self.original_coords.copy()

        # --- Widget central ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # --- Panel de controles ---
        control_panel = QGroupBox("Controles")
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        control_panel.setFixedWidth(300)

        # --- Widget OpenGL ---
        self.gl_widget = OpenGLWidget(
            self.current_coords.tolist(),
            triangle_indices.tolist() if hasattr(triangle_indices, 'tolist') else triangle_indices,
            line_indices.tolist() if hasattr(line_indices, 'tolist') else line_indices
        )

        # --- Modo de visualización ---
        mode_group = QGroupBox("Modo de visualización")
        mode_layout = QVBoxLayout()
        mode_group.setLayout(mode_layout)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Sólido", "solid")
        self.mode_combo.addItem("Alámbrico", "wireframe")
        self.mode_combo.addItem("Combinado", "combined")
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        mode_layout.addWidget(self.mode_combo)
        control_layout.addWidget(mode_group)

        # --- Control de desplazamientos ---
        disp_group = QGroupBox("Desplazamientos")
        disp_layout = QVBoxLayout()
        disp_group.setLayout(disp_layout)

        self.disp_checkbox = QCheckBox("Mostrar desplazamientos")
        self.disp_checkbox.setEnabled(self.disp_array is not None)
        self.disp_checkbox.stateChanged.connect(self.toggle_desplazamientos)
        disp_layout.addWidget(self.disp_checkbox)

        self.factor_slider = QSlider(Qt.Orientation.Horizontal)
        self.factor_slider.setRange(0, 1000)
        self.factor_slider.setValue(100)
        self.factor_slider.setEnabled(False)
        self.factor_slider.valueChanged.connect(self.update_desplazamientos)
        disp_layout.addWidget(QLabel("Factor de amplificación:"))
        disp_layout.addWidget(self.factor_slider)

        control_layout.addWidget(disp_group)

        # --- Grosor de línea ---
        width_group = QGroupBox("Grosor de línea")
        width_layout = QVBoxLayout()
        width_group.setLayout(width_layout)

        self.width_label = QLabel(f"Grosor actual: {self.gl_widget.line_width:.1f}")
        width_layout.addWidget(self.width_label)

        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setRange(1, 100)
        width_slider.setValue(int(self.gl_widget.line_width * 10))
        width_slider.valueChanged.connect(self.change_line_width)
        width_layout.addWidget(width_slider)

        control_layout.addWidget(width_group)

        # --- Cámara ---
        camera_group = QGroupBox("Cámara")
        camera_layout = QVBoxLayout()
        camera_group.setLayout(camera_layout)
        reset_btn = QPushButton("Resetear cámara")
        reset_btn.clicked.connect(self.gl_widget.reset_camera)
        camera_layout.addWidget(reset_btn)
        control_layout.addWidget(camera_group)

        # --- Color de fondo ---
        appearance_group = QGroupBox("Apariencia")
        appearance_layout = QVBoxLayout()
        appearance_group.setLayout(appearance_layout)
        appearance_layout.addWidget(QLabel("Color de fondo:"))

        self.bg_color_combo = QComboBox()
        self.bg_color_combo.addItem("Gris oscuro", QColor(25, 25, 25))
        self.bg_color_combo.addItem("Blanco", QColor(255, 255, 255))
        self.bg_color_combo.addItem("Negro", QColor(0, 0, 0))
        self.bg_color_combo.addItem("Azul oscuro", QColor(10, 20, 40))
        self.bg_color_combo.currentIndexChanged.connect(self.change_bg_color)
        appearance_layout.addWidget(self.bg_color_combo)

        control_layout.addWidget(appearance_group)

        # --- Información de controles ---
        info_group = QGroupBox("Controles")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        info_layout.addWidget(QLabel("Rotar: Botón izquierdo + arrastrar"))
        info_layout.addWidget(QLabel("Trasladar: Botón derecho + arrastrar"))
        info_layout.addWidget(QLabel("Zoom: Rueda del ratón"))
        control_layout.addWidget(info_group)
        control_layout.addStretch()

        # --- Añadir widgets al layout principal ---
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.gl_widget, 1)

        # --- Estado inicial ---
        self.gl_widget.set_mode("combined")
        self.mode_combo.setCurrentIndex(2)

        # Aplicar estado inicial de desplazamientos
        self.toggle_desplazamientos(self.disp_checkbox.checkState().value)

    # --- Métodos de control ---

    def toggle_desplazamientos(self, state):
        """Activa/desactiva la visualización de desplazamientos"""
        if state == Qt.CheckState.Checked.value and self.disp_array is not None:
            self.factor_slider.setEnabled(True)
            self.update_desplazamientos(self.factor_slider.value())
        else:
            self.factor_slider.setEnabled(False)
            self._reset_to_original()

    def _reset_to_original(self):
        """Restaura las coordenadas originales sin desplazamientos"""
        self.current_coords = self.original_coords.copy()
        self.gl_widget.update_coords(self.current_coords.tolist())

    def update_desplazamientos(self, value):
        if not self.disp_checkbox.isChecked() or self.disp_array is None:
            return

        self.current_coords = self.original_coords + value * self.disp_array
        self.gl_widget.update_coords(self.current_coords)

    def change_mode(self, index):
        mode = self.mode_combo.itemData(index)
        self.gl_widget.set_mode(mode)

    def change_line_width(self, value):
        line_width = value / 10.0
        self.gl_widget.set_line_width(line_width)
        self.width_label.setText(f"Grosor actual: {line_width:.1f}")

    def change_bg_color(self, index):
        color = self.bg_color_combo.itemData(index)
        self.gl_widget.set_bg_color(color)

if __name__ == '__main__':
    lector = Lector()
    lector.abrir_carpeta(r'./Para Visualizaciones/3D')
    print("Total de modelos:", lector.total_modelos)

    doc = lector.obtener_modelo(-1)
    coords_original, elements_original = doc["msh"]
    desplazamientos_original = doc["res"].get("desplazamientos")
    
    # Filtrar solo superficie visible
    coords, triangle_indices, line_indices, node_map = filtrar_elementos_visibles(coords_original, elements_original)
    
    # Mapear desplazamientos a nodos visibles
    desplazamientos = mapear_desplazamientos(desplazamientos_original, node_map)

    app = QApplication(sys.argv)
    window = MainWindow(coords, triangle_indices, line_indices, desplazamientos)
    window.show()
    sys.exit(app.exec())