import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QGroupBox, QLabel,
                             QComboBox, QSlider, QCheckBox, QStackedWidget, 
                             QToolButton, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QFont
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Widget OpenGL ---
        self.gl_widget = OpenGLWidget(
            self.current_coords.tolist(),
            triangle_indices.tolist() if hasattr(triangle_indices, 'tolist') else triangle_indices,
            line_indices.tolist() if hasattr(line_indices, 'tolist') else line_indices
        )

        # --- Panel lateral con pestañas ---
        self.side_panel = self._create_side_panel()
        main_layout.addWidget(self.side_panel)
        main_layout.addWidget(self.gl_widget, 1)

        # --- Estado inicial ---
        self.gl_widget.set_mode("combined")
        self.toggle_desplazamientos(self.disp_checkbox.checkState().value)

    def _create_side_panel(self):
        """Crea el panel lateral con pestañas con iconos"""
        side_panel = QWidget()
        side_panel.setFixedWidth(320)
        side_panel.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-right: 1px solid #1a1a1a;
            }
        """)
        
        panel_layout = QHBoxLayout(side_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # --- Barra de iconos lateral ---
        icon_bar = self._create_icon_bar()
        panel_layout.addWidget(icon_bar)

        # --- Área de contenido ---
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: transparent;
                border: none;
            }
        """)
        panel_layout.addWidget(self.content_stack)

        # --- Añadir páginas al stack ---
        self.visualization_page = self._create_visualization_page()
        self.displacements_page = self._create_displacements_page()
        
        self.content_stack.addWidget(self.visualization_page)
        self.content_stack.addWidget(self.displacements_page)

        return side_panel

    def _create_icon_bar(self):
        """Crea la barra lateral de iconos"""
        icon_bar = QWidget()
        icon_bar.setFixedWidth(60)
        icon_bar.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-right: 1px solid #0a0a0a;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 10px;
                color: #ffffff;
                border-radius: 4px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #3a3a3a;
            }
            QToolButton:checked {
                background-color: #2b2b2b;
                border-left: 3px solid #0d7dd6;
            }
        """)
        
        icon_layout = QVBoxLayout(icon_bar)
        icon_layout.setContentsMargins(5, 15, 5, 15)
        icon_layout.setSpacing(5)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Botón de Visualización
        self.vis_btn = QToolButton()
        self.vis_btn.setIcon(QIcon("icons/camara.svg"))
        self.vis_btn.setToolTip("Visualización")
        self.vis_btn.setCheckable(True)
        self.vis_btn.setChecked(True)
        self.vis_btn.setFixedSize(50, 50)
        self.vis_btn.setIconSize(QSize(24, 24))
        self.vis_btn.clicked.connect(lambda: self._switch_page(0))
        icon_layout.addWidget(self.vis_btn)

        # Botón de Desplazamientos
        self.disp_btn = QToolButton()
        self.disp_btn.setIcon(QIcon("icons/desp.svg"))
        self.disp_btn.setToolTip("Desplazamientos")
        self.disp_btn.setCheckable(True)
        self.disp_btn.setFixedSize(50, 50)
        self.disp_btn.setIconSize(QSize(24, 24))
        self.disp_btn.clicked.connect(lambda: self._switch_page(1))
        icon_layout.addWidget(self.disp_btn)

        icon_layout.addStretch()

        return icon_bar

    def _switch_page(self, page_index):
        """Cambia entre páginas del stack"""
        self.vis_btn.setChecked(False)
        self.disp_btn.setChecked(False)
        
        if page_index == 0:
            self.vis_btn.setChecked(True)
        elif page_index == 1:
            self.disp_btn.setChecked(True)
        
        self.content_stack.setCurrentIndex(page_index)

    def _create_visualization_page(self):
        """Crea la página de configuración de visualización"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
            }
            QGroupBox {
                color: #e0e0e0;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #404040;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #b0b0b0;
            }
            QLabel {
                background-color: transparent;
                border: none;
                padding: 3px;
                color: #b0b0b0;
                font-size: 11px;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #505050;
                color: #e0e0e0;
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QComboBox:hover {
                border: 1px solid #707070;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QSlider::groove:horizontal {
                background: #1a1a1a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0d7dd6;
                border: 1px solid #0a6bb5;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #1a8ae6;
            }
            QSlider::sub-page:horizontal {
                background: #0d7dd6;
                border-radius: 2px;
            }
        """)
        
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # --- Título de la página ---
        title = QLabel("Configuración de Visualización")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        layout.addWidget(title)

        # --- Modo de visualización ---
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
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        mode_layout.addWidget(self.mode_combo)
        layout.addWidget(mode_group)

        # --- Grosor de línea ---
        width_group = QGroupBox("Grosor de Líneas")
        width_layout = QVBoxLayout(width_group)
        width_layout.setSpacing(8)

        initial_width = getattr(self.gl_widget, 'line_width', 2.0)
        self.width_label = QLabel(f"Grosor: {initial_width:.1f} px")
        self.width_label.setStyleSheet("font-size: 11px; color: #e0e0e0; font-weight: 600;")
        width_layout.addWidget(self.width_label)

        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setRange(1, 100)
        width_slider.setValue(int(initial_width * 10))
        width_slider.valueChanged.connect(self.change_line_width)
        width_layout.addWidget(width_slider)

        layout.addWidget(width_group)

        # --- Color de fondo ---
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
        self.bg_color_combo.currentIndexChanged.connect(self.change_bg_color)
        appearance_layout.addWidget(self.bg_color_combo)

        layout.addWidget(appearance_group)

        # --- Cámara ---
        camera_group = QGroupBox("Control de Cámara")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(8)
        
        reset_btn = QPushButton("Resetear Vista")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #505050;
                padding: 8px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #454545;
                border: 1px solid #707070;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        reset_btn.clicked.connect(self.gl_widget.reset_camera)
        camera_layout.addWidget(reset_btn)
        layout.addWidget(camera_group)

        layout.addStretch()
        return page

    def _create_displacements_page(self):
        """Crea la página de configuración de desplazamientos"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
            }
            QGroupBox {
                color: #e0e0e0;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #404040;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #b0b0b0;
            }
            QCheckBox {
                background-color: transparent;
                color: #e0e0e0;
                padding: 6px;
                font-size: 11px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #505050;
                background-color: #3a3a3a;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #707070;
            }
            QCheckBox::indicator:checked {
                background-color: #0d7dd6;
                border: 1px solid #0a6bb5;
            }
            QLabel {
                background-color: transparent;
                border: none;
                padding: 3px;
                color: #b0b0b0;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                background: #1a1a1a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0d7dd6;
                border: 1px solid #0a6bb5;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #1a8ae6;
            }
            QSlider::sub-page:horizontal {
                background: #0d7dd6;
                border-radius: 2px;
            }
        """)
        
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # --- Título de la página ---
        title = QLabel("Configuración de Desplazamientos")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        layout.addWidget(title)

        # --- Control de desplazamientos ---
        disp_group = QGroupBox("Control de Deformación")
        disp_layout = QVBoxLayout(disp_group)
        disp_layout.setSpacing(10)

        self.disp_checkbox = QCheckBox("Activar deformaciones")
        self.disp_checkbox.setEnabled(self.disp_array is not None)
        self.disp_checkbox.stateChanged.connect(self.toggle_desplazamientos)
        disp_layout.addWidget(self.disp_checkbox)

        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #404040; max-height: 1px;")
        disp_layout.addWidget(separator)

        amp_label = QLabel("Factor de amplificación:")
        amp_label.setStyleSheet("font-size: 11px; color: #b0b0b0; padding-top: 4px;")
        disp_layout.addWidget(amp_label)
        
        self.factor_slider = QSlider(Qt.Orientation.Horizontal)
        self.factor_slider.setRange(0, 1000)
        self.factor_slider.setValue(100)
        self.factor_slider.setEnabled(False)
        self.factor_slider.valueChanged.connect(self.update_desplazamientos)
        disp_layout.addWidget(self.factor_slider)

        self.factor_label = QLabel(f"Factor: {self.factor_slider.value()}")
        self.factor_label.setStyleSheet("font-size: 11px; color: #e0e0e0; font-weight: 600; padding: 4px;")
        disp_layout.addWidget(self.factor_label)
        self.factor_slider.valueChanged.connect(
            lambda value: self.factor_label.setText(f"Factor: {value}")
        )

        layout.addWidget(disp_group)

        layout.addStretch()
        return page

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
        self.width_label.setText(f"Grosor: {line_width:.1f} px")

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