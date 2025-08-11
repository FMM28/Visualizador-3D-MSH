import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QGroupBox, QLabel, 
                            QComboBox, QSlider)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat, QColor
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyrr import Matrix44
from msh import LectorMsh
from cameraController import Camera

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, coords, elements, parent=None):
        super().__init__(parent)
        self.coords = coords
        self.elements = elements
        self.camera = None
        self.mvp = None
        self.last_x, self.last_y = 0, 0
        self.current_mode = "solid"
        self.bg_color = (0.1, 0.1, 0.1)
        self.model_center = None
        self.model_radius = None
        self.shader_programs = {}
        self.vao = None
        self.vbo = None
        self.ibo = None
        self.line_width = 1.5
        
        # formato OpenGL
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
    
    def initializeGL(self):
        print("Inicializando OpenGL...")
        
        # Configurar funciones OpenGL
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        
        # Procesar datos del modelo
        coords_3d = []
        for point in self.coords:
            if len(point) == 2:
                coords_3d.append([point[0], point[1], 0.0])
            else:
                coords_3d.append(point)
        
        self.coords_array = np.array(coords_3d, dtype='f4')
        print(f"Coordenadas cargadas: {len(self.coords_array)} puntos")
        
        triangles = []
        for elem in self.elements:
            idxs = [i - 1 for i in elem]
            
            if len(idxs) == 3:
                triangles.append(idxs)
            elif len(idxs) == 4:
                triangles.append([idxs[0], idxs[1], idxs[2]])
                triangles.append([idxs[0], idxs[2], idxs[3]])
        
        self.triangles_array = np.array(triangles, dtype='i4').flatten()
        print(f"Triángulos cargados: {len(self.triangles_array)//3} triángulos")
        
        # Crear shaders con colores sólidos
        self.create_shaders()
        
        # Crear buffers
        self.create_buffers()
        
        # Configurar cámara
        self.model_center = np.array(self.coords_array.mean(axis=0))
        self.model_radius = np.linalg.norm(self.coords_array - self.model_center, axis=1).max() * 1.5
        self.camera = Camera(self.model_center, self.model_radius)
        print(f"Cámara configurada. Centro: {self.model_center}, Radio: {self.model_radius}")
    
    def create_shaders(self):
        # Vertex shader común
        vertex_shader_src = """
        #version 330 core
        uniform mat4 mvp;
        layout(location = 0) in vec3 in_position;
        void main() {
            gl_Position = mvp * vec4(in_position, 1.0);
        }
        """
        
        # Fragment shaders con colores sólidos sin iluminación
        frag_shaders = {
            "solid": """
            #version 330 core
            out vec4 frag_color;
            void main() {
                frag_color = vec4(0.2, 0.4, 0.8, 1.0); // Azul sólido
            }
            """,
            
            "wireframe": """
            #version 330 core
            out vec4 frag_color;
            void main() {
                frag_color = vec4(1.0, 0.2, 0.2, 1.0); // Rojo sólido
            }
            """
        }
        
        # Compilar shaders
        for name, frag_src in frag_shaders.items():
            try:
                vertex_shader = compileShader(vertex_shader_src, GL_VERTEX_SHADER)
                fragment_shader = compileShader(frag_src, GL_FRAGMENT_SHADER)
                self.shader_programs[name] = compileProgram(vertex_shader, fragment_shader)
                print(f"Shader {name} compilado exitosamente")
            except Exception as e:
                print(f"Error compilando shader {name}: {e}")
                if name != "solid":
                    self.shader_programs[name] = self.shader_programs.get("solid", None)
    
    def create_buffers(self):
        # Crear y configurar VBO para vértices
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_STATIC_DRAW)
        
        # Crear y configurar IBO para índices
        self.ibo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangles_array.nbytes, self.triangles_array, GL_STATIC_DRAW)
        
        # Crear VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Configurar atributos de vértices
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        # Posición (atributo 0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBindVertexArray(0)
        
        print("Buffers creados exitosamente")
    
    def paintGL(self):
        if not self.camera:
            return
            
        try:
            # Limpiar pantalla
            glClearColor(*self.bg_color, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Actualizar matriz MVP
            width, height = self.width(), self.height()
            ratio = width / height if height > 0 else 1.0
            
            view = self.camera.get_view_matrix()
            proj = Matrix44.perspective_projection(45.0, ratio, 0.1, self.camera.radius * 10.0)
            self.mvp = (proj * view).astype('f4')
            
            # Renderizar según el modo
            if self.current_mode == "solid":
                # Usar shader sólido
                shader = self.shader_programs["solid"]
                glUseProgram(shader)
                mvp_loc = glGetUniformLocation(shader, "mvp")
                if mvp_loc != -1:
                    glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, self.mvp)
                
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glBindVertexArray(self.vao)
                glDrawElements(GL_TRIANGLES, len(self.triangles_array), GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
            
            elif self.current_mode == "wireframe":
                # Usar shader alámbrico
                shader = self.shader_programs["wireframe"]
                glUseProgram(shader)
                mvp_loc = glGetUniformLocation(shader, "mvp")
                if mvp_loc != -1:
                    glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, self.mvp)
                
                glLineWidth(self.line_width)
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                glBindVertexArray(self.vao)
                glDrawElements(GL_TRIANGLES, len(self.triangles_array), GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
            
            elif self.current_mode == "combined":
                # Primero dibujar el sólido
                shader_solid = self.shader_programs["solid"]
                glUseProgram(shader_solid)
                mvp_loc_solid = glGetUniformLocation(shader_solid, "mvp")
                if mvp_loc_solid != -1:
                    glUniformMatrix4fv(mvp_loc_solid, 1, GL_FALSE, self.mvp)
                
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glBindVertexArray(self.vao)
                glDrawElements(GL_TRIANGLES, len(self.triangles_array), GL_UNSIGNED_INT, None)
                
                # Luego dibujar el alámbrico encima
                shader_wire = self.shader_programs["wireframe"]
                glUseProgram(shader_wire)
                mvp_loc_wire = glGetUniformLocation(shader_wire, "mvp")
                if mvp_loc_wire != -1:
                    glUniformMatrix4fv(mvp_loc_wire, 1, GL_FALSE, self.mvp)
                
                glLineWidth(self.line_width)
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                
                # IMPORTANTE: Volver a vincular el VAO para el alámbrico
                glBindVertexArray(self.vao)
                glDrawElements(GL_TRIANGLES, len(self.triangles_array), GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
            
            # Restaurar modo de polígono
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            
        except Exception as e:
            print(f"Error en renderizado: {e}")
    
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_x = event.position().x()
            self.last_y = event.position().y()
        elif event.button() == Qt.MouseButton.RightButton:
            self.last_x = event.position().x()
            self.last_y = event.position().y()
    
    def mouseMoveEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        dx = x - self.last_x
        dy = y - self.last_y
        self.last_x = x
        self.last_y = y
        
        buttons = event.buttons()
        if buttons & Qt.MouseButton.LeftButton:
            self.camera.rotate(dx, dy)
            self.update()
        elif buttons & Qt.MouseButton.RightButton:
            self.camera.pan(dx, dy)
            self.update()
    
    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        if delta != 0:
            self.camera.zoom(delta)
            self.update()
    
    def set_mode(self, mode):
        if mode in ["solid", "wireframe", "combined"]:
            self.current_mode = mode
            self.update()
    
    def set_line_width(self, width):
        self.line_width = width
        self.update()
    
    def reset_camera(self):
        if self.camera:
            self.camera.reset()
            self.update()
    
    def set_bg_color(self, color):
        self.bg_color = (color.redF(), color.greenF(), color.blueF())
        self.update()

# Ventana principal
class MainWindow(QMainWindow):
    def __init__(self, coords, elements):
        super().__init__()
        self.setWindowTitle("Visualizador 3D - Sólido y Alámbrico")
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
        self.mode_combo.addItem("Sólido (Azul)", "solid")
        self.mode_combo.addItem("Alámbrico (Rojo)", "wireframe")
        self.mode_combo.addItem("Combinado (Azul + Rojo)", "combined")
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        mode_layout.addWidget(self.mode_combo)
        
        # Control de grosor de línea simplificado
        width_group = QGroupBox("Grosor de línea")
        width_layout = QVBoxLayout()
        width_group.setLayout(width_layout)
        
        width_label = QLabel(f"Grosor actual: {self.gl_widget.line_width:.1f}")
        width_layout.addWidget(width_label)
        
        width_slider = QSlider(Qt.Orientation.Horizontal)
        width_slider.setRange(1, 50)  # 1 a 50 representa 0.1 a 5.0
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
        # Convertir valor del slider (1-50) a ancho de línea (0.1-5.0)
        line_width = value / 10.0
        self.gl_widget.set_line_width(line_width)
        label.setText(f"Grosor actual: {line_width:.1f}")
    
    def change_bg_color(self, index):
        color = self.bg_color_combo.itemData(index)
        self.gl_widget.set_bg_color(color)

if __name__ == '__main__':
    
    lector = LectorMsh()

    lector.abrir_carpeta(r'C:\Users\frank\Downloads\Para Visualizaciones\Para Visualizaciones\3D')
    # C:\Users\frank\Downloads\Para Visualizaciones\Para Visualizaciones\2D\Agrietamiento
    # C:\Users\frank\Downloads\Para Visualizaciones\Para Visualizaciones\3D
    print("Total de modelos:", lector.total_modelos)

    lector.ir_al_ultimo()
    coords, elements = lector.obtener_modelo_actual()
    
    # Iniciar aplicación
    app = QApplication(sys.argv)
    
    # Configuración global de OpenGL
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSamples(4)
    fmt.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    window = MainWindow(coords, elements)
    window.show()
    sys.exit(app.exec())