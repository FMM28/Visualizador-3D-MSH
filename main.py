import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QGroupBox, QLabel, 
                            QComboBox, QSlider)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from msh import LectorMsh
from OpenGLWidget import OpenGLWidget

# Ventana principal
class MainWindow(QMainWindow):
    def __init__(self, coords, elements):
        super().__init__()
        self.setWindowTitle("Visualizador 3D")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()
        
        # Crear widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Diseño principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Panel izquierdo para controles
        control_panel = QGroupBox("Controles")
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        control_panel.setFixedWidth(300)
        
        # Widget OpenGL
        self.gl_widget = OpenGLWidget(coords, elements)
        
        # Botones de modo
        mode_group = QGroupBox("Modo de visualización")
        mode_layout = QVBoxLayout()
        mode_group.setLayout(mode_layout)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Sólido", "solid")
        self.mode_combo.addItem("Alámbrico", "wireframe")
        self.mode_combo.addItem("Combinado", "combined")
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        mode_layout.addWidget(self.mode_combo)
        
        # Control de grosor de línea
        width_group = QGroupBox("Grosor de línea")
        width_layout = QVBoxLayout()
        width_group.setLayout(width_layout)
        
        width_label = QLabel(f"Grosor actual: {self.gl_widget.line_width:.1f}")
        width_layout.addWidget(width_label)
        
        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setRange(1, 100)
        width_slider.setValue(int(self.gl_widget.line_width * 10))
        width_slider.valueChanged.connect(lambda value: self.change_line_width(value, width_label))
        width_layout.addWidget(width_slider)
        
        # Controles de cámara
        camera_group = QGroupBox("Cámara")
        camera_layout = QVBoxLayout()
        camera_group.setLayout(camera_layout)
        
        btn_reset = QPushButton("Resetear cámara")
        btn_reset.clicked.connect(self.gl_widget.reset_camera)
        camera_layout.addWidget(btn_reset)
        
        # Controles de apariencia
        appearance_group = QGroupBox("Apariencia")
        appearance_layout = QVBoxLayout()
        appearance_group.setLayout(appearance_layout)
        
        bg_label = QLabel("Color de fondo:")
        appearance_layout.addWidget(bg_label)
        
        self.bg_color_combo = QComboBox()
        self.bg_color_combo.addItem("Gris oscuro", QColor(25, 25, 25))
        self.bg_color_combo.addItem("Blanco", QColor(255, 255, 255))
        self.bg_color_combo.addItem("Negro", QColor(0, 0, 0))
        self.bg_color_combo.addItem("Azul oscuro", QColor(10, 20, 40))
        self.bg_color_combo.currentIndexChanged.connect(self.change_bg_color)
        appearance_layout.addWidget(self.bg_color_combo)
        
        # Información de controles
        info_group = QGroupBox("Controles")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        
        info_layout.addWidget(QLabel("Rotar: Botón izquierdo ratón + arrastrar"))
        info_layout.addWidget(QLabel("Trasladar: Botón derecho ratón + arrastrar"))
        info_layout.addWidget(QLabel("Zoom: Rueda ratón"))
        
        # Añadir grupos al panel de control
        control_layout.addWidget(mode_group)
        control_layout.addWidget(width_group)
        control_layout.addWidget(camera_group)
        control_layout.addWidget(appearance_group)
        control_layout.addWidget(info_group)
        control_layout.addStretch()
        
        # Añadir widgets al layout principal
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.gl_widget, 1)
        
        # Estado inicial
        self.gl_widget.set_mode("combined")
        self.mode_combo.setCurrentIndex(2)
    
    def change_mode(self, index):
        mode = self.mode_combo.itemData(index)
        self.gl_widget.set_mode(mode)
    
    def change_line_width(self, value, label):
        line_width = value / 10.0
        self.gl_widget.set_line_width(line_width)
        label.setText(f"Grosor actual: {line_width:.1f}")
    
    def change_bg_color(self, index):
        color = self.bg_color_combo.itemData(index)
        self.gl_widget.set_bg_color(color)

if __name__ == '__main__':
    
    lector = LectorMsh()

    lector.abrir_carpeta(r'./Para Visualizaciones/3D')

    print("Total de modelos:", lector.total_modelos)

    lector.ir_al_ultimo()
    coords, elements = lector.obtener_modelo_actual()
    
    # Iniciar aplicación
    app = QApplication(sys.argv)
    
    window = MainWindow(coords, elements)
    window.show()
    sys.exit(app.exec())