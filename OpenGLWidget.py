import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyrr import Matrix44
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from cameraController import Camera

class OpenGLWidget(QOpenGLWidget):
    # Constantes de shader
    VERTEX_SHADER = """
    #version 330 core
    uniform mat4 mvp;
    layout(location = 0) in vec3 in_position;
    void main() {
        gl_Position = mvp * vec4(in_position, 1.0);
    }
    """
    
    GEOMETRY_SHADER = """
    #version 330 core
    layout(lines) in;
    layout(triangle_strip, max_vertices = 4) out;
    
    uniform float line_width;
    uniform float aspect_ratio;
    
    void main() {
        vec4 p0 = gl_in[0].gl_Position;
        vec4 p1 = gl_in[1].gl_Position;
        
        if (abs(p0.w) < 1e-6 || abs(p1.w) < 1e-6) return;
        
        vec3 ndc0 = p0.xyz / p0.w;
        vec3 ndc1 = p1.xyz / p1.w;
        
        vec2 dir = ndc1.xy - ndc0.xy;
        float len_dir = length(dir);
        if (len_dir < 1e-6) return;
        
        dir /= len_dir;
        vec2 normal = normalize(vec2(-dir.y, dir.x / aspect_ratio)) * line_width * 0.002;
        
        gl_Position = vec4((ndc0.xy - normal) * p0.w, p0.z, p0.w); EmitVertex();
        gl_Position = vec4((ndc0.xy + normal) * p0.w, p0.z, p0.w); EmitVertex();
        gl_Position = vec4((ndc1.xy - normal) * p1.w, p1.z, p1.w); EmitVertex();
        gl_Position = vec4((ndc1.xy + normal) * p1.w, p1.z, p1.w); EmitVertex();
        EndPrimitive();
    }
    """
    
    FRAGMENT_SHADERS = {
        "solid": "out vec4 frag_color; void main() { frag_color = vec4(0.2, 0.2, 0.2, 1.0); }",
        "line": "out vec4 frag_color; void main() { frag_color = vec4(1.0, 0.2, 0.2, 1.0); }"
    }

    def __init__(self, coords, elements, parent=None):
        super().__init__(parent)
        self.coords = coords
        self.elements = elements
        
        # Estado
        self.camera = None
        self.last_x, self.last_y = 0, 0
        self.current_mode = "solid"
        self.bg_color = (0.1, 0.1, 0.1)
        self.line_width = 1
        
        # Datos del modelo
        self.model_center = None
        self.model_radius = None
        
        # Recursos OpenGL
        self.shader_programs = {}
        self.buffers = self._init_buffer_structure()
        
        # Flags
        self.gl_initialized = False
        self.has_valid_data = False
        
        self._setup_opengl_format()
    
    def _init_buffer_structure(self):
        """Inicializa la estructura de buffers"""
        return {
            'solid': {'vao': None, 'vbo': None, 'ibo': None, 'count': 0},
            'line': {'vao': None, 'vbo': None, 'count': 0}
        }
    
    def _setup_opengl_format(self):
        """Configura el formato OpenGL"""
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
    
    def initializeGL(self):
        print("Inicializando OpenGL...")
        
        # Configuración OpenGL básica
        self._configure_opengl_state()
        
        # Procesar datos y crear recursos
        self._process_geometry()
        
        if self.has_valid_data:
            self._create_shaders()
            self._create_buffers()
            self._setup_camera()
            print(f"Inicialización completa. Triángulos: {self.buffers['solid']['count']//3}, Líneas: {self.buffers['line']['count']//2}")
        else:
            print("No se pudieron procesar los datos de geometría")
            self._create_minimal_setup()
        
        self.gl_initialized = True
    
    def _configure_opengl_state(self):
        """Configura el estado inicial de OpenGL"""
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_POLYGON_OFFSET_FILL)
    
    def _validate_input_data(self):
        """Valida que los datos de entrada sean correctos"""
        if not self.coords or not self.elements:
            print("Faltan coordenadas o elementos")
            return False
        
        try:
            # Validar coordenadas
            for i, coord in enumerate(self.coords):
                if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                    print(f"Coordenada inválida en índice {i}: {coord}")
                    return False
                
                for val in coord[:3]:
                    float(val)
            
            # Validar elementos
            max_coord_index = len(self.coords) - 1
            for i, elem in enumerate(self.elements):
                if not isinstance(elem, (list, tuple)) or len(elem) < 3:
                    print(f"Elemento inválido en índice {i}: {elem}")
                    return False
                
                for node_idx in elem:
                    if not isinstance(node_idx, int) or not (0 <= node_idx <= max_coord_index):
                        print(f"Índice de nodo inválido en elemento {i}: {node_idx}")
                        return False
            
            return True
            
        except (ValueError, TypeError) as e:
            print(f"Error validando datos: {e}")
            return False
    
    def _process_geometry(self):
        """Procesa coordenadas y elementos para crear triángulos y líneas"""
        try:
            if not self._validate_input_data():
                self.has_valid_data = False
                return
            
            # Normalizar coordenadas a 3D
            self.coords_array = self._normalize_coords_to_3d()
            
            # Procesar elementos
            triangles, edges = self._process_elements()
            
            if not triangles:
                print("No se generaron triángulos válidos")
                self.has_valid_data = False
                return
            
            # Almacenar datos procesados
            self.triangles_array = np.array(triangles, dtype=np.uint32).flatten()
            self.buffers['solid']['count'] = len(self.triangles_array)
            
            # Crear geometría de líneas
            self._create_line_geometry(edges)
            
        except Exception as e:
            print(f"Error procesando geometría: {e}")
            self.has_valid_data = False
    
    def _normalize_coords_to_3d(self):
        """Normaliza coordenadas a 3D"""
        coords_3d = []
        for point in self.coords:
            if len(point) == 2:
                coords_3d.append([float(point[0]), float(point[1]), 0.0])
            else:
                coords_3d.append([float(point[0]), float(point[1]), float(point[2] if len(point) > 2 else 0.0)])
        
        coords_array = np.array(coords_3d, dtype=np.float32)
        
        if coords_array.size == 0 or len(coords_array.shape) != 2 or coords_array.shape[1] != 3:
            raise ValueError(f"Array de coordenadas inválido: shape={coords_array.shape}")
        
        return coords_array
    
    def _process_elements(self):
        """Procesa elementos en triángulos y aristas"""
        triangles = []
        edges = set()
        
        for elem in self.elements:
            elem_triangles = self._element_to_triangles(elem)
            triangles.extend(elem_triangles)
            
            # Generar aristas
            for tri in elem_triangles:
                edges.update([
                    tuple(sorted((tri[0], tri[1]))),
                    tuple(sorted((tri[1], tri[2]))),
                    tuple(sorted((tri[2], tri[0])))
                ])
        
        return triangles, edges
    
    def _create_line_geometry(self, edges):
        """Crea la geometría de líneas a partir de las aristas"""
        line_vertices = []
        for edge in edges:
            if edge[0] < len(self.coords_array) and edge[1] < len(self.coords_array):
                line_vertices.extend(self.coords_array[edge[0]])
                line_vertices.extend(self.coords_array[edge[1]])
        
        if line_vertices:
            self.line_vertices = np.array(line_vertices, dtype=np.float32)
            self.buffers['line']['count'] = len(edges) * 2
            self.has_valid_data = True
        else:
            print("No se generaron líneas válidas")
            self.has_valid_data = False
    
    def _element_to_triangles(self, elem):
        """Convierte un elemento en triángulos según su tipo"""
        try:
            elem_len = len(elem)
            
            if elem_len == 3:  # Triángulo
                return [elem]
            elif elem_len == 4:  # Tetraedro o cuadrilátero
                if self._is_3d_element(elem):
                    return self._tetrahedron_faces(elem)
                else:
                    return [[elem[0], elem[1], elem[2]], [elem[0], elem[2], elem[3]]]
            elif elem_len == 8:  # Hexaedro
                return self._hexahedron_faces(elem)
            elif elem_len > 4:  # Polígono general - triangulación en abanico
                return [[elem[0], elem[i], elem[i+1]] for i in range(1, elem_len-1)]
            else:
                return []
        except Exception as e:
            print(f"Error procesando elemento {elem}: {e}")
            return []
    
    def _is_3d_element(self, elem):
        """Determina si un elemento de 4 nodos es 3D (tetraedro) o 2D (cuadrilátero)"""
        try:
            if len(self.coords_array) <= max(elem):
                return False
            coords = self.coords_array[elem]
            v1, v2, v3 = coords[1:4] - coords[0]
            volume = abs(np.dot(v1, np.cross(v2, v3))) / 6.0
            return volume > 1e-10
        except Exception:
            return False
    
    def _tetrahedron_faces(self, elem):
        """Caras de un tetraedro"""
        return [
            [elem[0], elem[1], elem[2]], [elem[0], elem[1], elem[3]],
            [elem[0], elem[2], elem[3]], [elem[1], elem[2], elem[3]]
        ]
    
    def _hexahedron_faces(self, elem):
        """Caras de un hexaedro"""
        return [
            [elem[0], elem[1], elem[2]], [elem[0], elem[2], elem[3]],
            [elem[4], elem[5], elem[6]], [elem[4], elem[6], elem[7]],
            [elem[0], elem[3], elem[7]], [elem[0], elem[7], elem[4]],
            [elem[1], elem[2], elem[6]], [elem[1], elem[6], elem[5]],
            [elem[0], elem[1], elem[5]], [elem[0], elem[5], elem[4]],
            [elem[3], elem[2], elem[6]], [elem[3], elem[6], elem[7]]
        ]
    
    def _create_minimal_setup(self):
        """Crea una configuración mínima cuando no hay datos válidos"""
        self.model_center = np.array([0.0, 0.0, 0.0])
        self.model_radius = 5.0
        self.camera = Camera(self.model_center, self.model_radius)
        
        try:
            self._create_shaders()
        except Exception as e:
            print(f"Error creando shaders mínimos: {e}")
    
    def _create_shaders(self):
        """Crea todos los shaders necesarios"""
        try:
            vs = compileShader(self.VERTEX_SHADER, GL_VERTEX_SHADER)
            
            # Shader sólido
            fs_solid = compileShader(f"#version 330 core\n{self.FRAGMENT_SHADERS['solid']}", GL_FRAGMENT_SHADER)
            self.shader_programs["solid"] = compileProgram(vs, fs_solid)
            
            # Shader de líneas con geometry shader
            gs = compileShader(self.GEOMETRY_SHADER, GL_GEOMETRY_SHADER)
            fs_line = compileShader(f"#version 330 core\n{self.FRAGMENT_SHADERS['line']}", GL_FRAGMENT_SHADER)
            self.shader_programs["line"] = compileProgram(vs, gs, fs_line)
            
            print("Shaders compilados exitosamente")
            
        except Exception as e:
            print(f"Error compilando shaders: {e}")
    
    def _create_buffers(self):
        """Crea todos los buffers OpenGL"""
        if not self.has_valid_data:
            return
        
        self._create_solid_buffers()
        self._create_line_buffers()
        
        glBindVertexArray(0)
        print("Buffers creados exitosamente")
    
    def _create_solid_buffers(self):
        """Crea buffers para renderizado sólido"""
        solid_buf = self.buffers['solid']
        solid_buf['vao'] = glGenVertexArrays(1)
        solid_buf['vbo'] = glGenBuffers(1)
        solid_buf['ibo'] = glGenBuffers(1)
        
        glBindVertexArray(solid_buf['vao'])
        
        # VBO coordenadas
        glBindBuffer(GL_ARRAY_BUFFER, solid_buf['vbo'])
        glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # IBO índices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, solid_buf['ibo'])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangles_array.nbytes, self.triangles_array, GL_STATIC_DRAW)
    
    def _create_line_buffers(self):
        """Crea buffers para renderizado de líneas"""
        line_buf = self.buffers['line']
        line_buf['vao'] = glGenVertexArrays(1)
        line_buf['vbo'] = glGenBuffers(1)
        
        glBindVertexArray(line_buf['vao'])
        glBindBuffer(GL_ARRAY_BUFFER, line_buf['vbo'])
        glBufferData(GL_ARRAY_BUFFER, self.line_vertices.nbytes, self.line_vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
    
    def _update_buffers(self):
        """Actualiza los buffers OpenGL con nuevas coordenadas"""
        if not self.gl_initialized or not self.has_valid_data:
            return
        
        try:
            # Actualizar buffer sólido
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers['solid']['vbo'])
            glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_STATIC_DRAW)
            
            # Regenerar líneas
            self._regenerate_line_buffers()
            
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        except Exception as e:
            print(f"Error actualizando buffers: {e}")
    
    def _regenerate_line_buffers(self):
        """Regenera los buffers de líneas"""
        _, edges = self._process_elements()
        line_vertices = []
        
        for edge in edges:
            if edge[0] < len(self.coords_array) and edge[1] < len(self.coords_array):
                line_vertices.extend(self.coords_array[edge[0]])
                line_vertices.extend(self.coords_array[edge[1]])
        
        if line_vertices:
            self.line_vertices = np.array(line_vertices, dtype=np.float32)
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers['line']['vbo'])
            glBufferData(GL_ARRAY_BUFFER, self.line_vertices.nbytes, self.line_vertices, GL_STATIC_DRAW)
    
    def _setup_camera(self):
        """Configura la cámara basada en el modelo"""
        try:
            if self.coords_array.size == 0:
                self.model_center = np.array([0.0, 0.0, 0.0])
                self.model_radius = 5.0
            else:
                self.model_center = self.coords_array.mean(axis=0)
                distances = np.linalg.norm(self.coords_array - self.model_center, axis=1)
                self.model_radius = max(distances.max() * 1.5, 1.0)
            
            self.camera = Camera(self.model_center, self.model_radius)
        except Exception as e:
            print(f"Error configurando cámara: {e}")
            self.model_center = np.array([0.0, 0.0, 0.0])
            self.model_radius = 5.0
            self.camera = Camera(self.model_center, self.model_radius)
    
    def _set_shader_uniforms(self, shader, mvp_matrix, shader_type):
        """Configura los uniformes del shader"""
        mvp_loc = glGetUniformLocation(shader, "mvp")
        if mvp_loc != -1:
            glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, mvp_matrix)
        
        if shader_type == "line":
            width_loc = glGetUniformLocation(shader, "line_width")
            aspect_loc = glGetUniformLocation(shader, "aspect_ratio")
            
            if width_loc != -1:
                glUniform1f(width_loc, self.line_width)
            if aspect_loc != -1:
                aspect = self.width() / max(self.height(), 1)
                glUniform1f(aspect_loc, aspect)
    
    def _render_solid(self, mvp_matrix):
        """Renderiza el modelo sólido"""
        if not self.has_valid_data or "solid" not in self.shader_programs:
            return
            
        glPolygonOffset(1.0, 1.0)
        glEnable(GL_POLYGON_OFFSET_FILL)
        
        shader = self.shader_programs["solid"]
        glUseProgram(shader)
        self._set_shader_uniforms(shader, mvp_matrix, "solid")
        
        glBindVertexArray(self.buffers['solid']['vao'])
        glDrawElements(GL_TRIANGLES, self.buffers['solid']['count'], GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def _render_wireframe(self, mvp_matrix):
        """Renderiza el modelo en alambre"""
        if not self.has_valid_data or "line" not in self.shader_programs:
            return
            
        glDisable(GL_POLYGON_OFFSET_FILL)
        
        shader = self.shader_programs["line"]
        glUseProgram(shader)
        self._set_shader_uniforms(shader, mvp_matrix, "line")
        
        glBindVertexArray(self.buffers['line']['vao'])
        glDrawArrays(GL_LINES, 0, self.buffers['line']['count'])
        glBindVertexArray(0)
    
    def paintGL(self):
        """Renderiza la escena"""
        if not self.camera:
            return
        
        # Limpiar buffers
        glClearColor(*self.bg_color, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self.has_valid_data:
            return
        
        # Calcular matriz MVP
        mvp_matrix = self._calculate_mvp_matrix()
        
        # Renderizar según modo
        try:
            if self.current_mode == "solid":
                self._render_solid(mvp_matrix)
            elif self.current_mode == "wireframe":
                self._render_wireframe(mvp_matrix)
            elif self.current_mode == "combined":
                self._render_solid(mvp_matrix)
                glDepthMask(GL_FALSE)
                self._render_wireframe(mvp_matrix)
                glDepthMask(GL_TRUE)
                
        except Exception as e:
            print(f"Error en renderizado: {e}")
    
    def _calculate_mvp_matrix(self):
        """Calcula la matriz MVP"""
        width, height = self.width(), max(self.height(), 1)
        ratio = width / height
        
        view = self.camera.get_view_matrix()
        proj = Matrix44.perspective_projection(45.0, ratio, 0.1, self.camera.radius * 10.0)
        return (proj * view).astype(np.float32)
    
    def resizeGL(self, w, h):
        """Maneja el redimensionamiento del widget"""
        glViewport(0, 0, w, h)
    
    def mousePressEvent(self, event):
        """Maneja el evento de presión del mouse"""
        self.last_x = event.position().x()
        self.last_y = event.position().y()
    
    def mouseMoveEvent(self, event):
        """Maneja el movimiento del mouse"""
        if not self.camera:
            return
            
        x, y = event.position().x(), event.position().y()
        dx, dy = x - self.last_x, y - self.last_y
        self.last_x, self.last_y = x, y
        
        buttons = event.buttons()
        if buttons & Qt.MouseButton.LeftButton:
            self.camera.rotate(dx, dy)
            self.update()
        elif buttons & Qt.MouseButton.RightButton:
            self.camera.pan(dx, dy)
            self.update()
    
    def wheelEvent(self, event):
        """Maneja el evento de la rueda del mouse"""
        if self.camera:
            delta = event.angleDelta().y() / 120
            if delta != 0:
                self.camera.zoom(delta)
                self.update()
    
    # Métodos públicos
    def set_mode(self, mode):
        """Establece el modo de renderizado"""
        if mode in ["solid", "wireframe", "combined"]:
            self.current_mode = mode
            self.update()
    
    def set_line_width(self, width):
        """Establece el grosor de línea"""
        self.line_width = max(0.1, width)
        self.update()
    
    def reset_camera(self):
        """Resetea la cámara a su posición inicial"""
        if self.camera:
            self.camera.reset()
            self.update()
    
    def set_bg_color(self, color):
        """Establece el color de fondo"""
        self.bg_color = (color.redF(), color.greenF(), color.blueF())
        self.update()
    
    def update_coords(self, new_coords, update_camera=False):
        """Actualiza las coordenadas del modelo"""
        self.coords = new_coords
        
        if not self._validate_input_data():
            print("Las nuevas coordenadas no son válidas")
            return
        
        # Reprocesar geometría
        self._process_geometry()
        
        # Actualizar recursos si OpenGL está inicializado
        if self.gl_initialized and self.has_valid_data:
            self._update_buffers()
            
            if update_camera:
                self._setup_camera()
            
            self.update()
    
    def update_camera_for_current_model(self):
        """Recalcula la cámara para el modelo actual"""
        if self.gl_initialized and self.has_valid_data:
            self._setup_camera()
            self.update()
    
    def __del__(self):
        """Limpieza de recursos OpenGL"""
        if hasattr(self, 'buffers'):
            self._cleanup_opengl_resources()
    
    def _cleanup_opengl_resources(self):
        """Limpia los recursos OpenGL"""
        for buf_type in self.buffers.values():
            if buf_type.get('vao'):
                glDeleteVertexArrays(1, [buf_type['vao']])
            if buf_type.get('vbo'):
                glDeleteBuffers(1, [buf_type['vbo']])
            if buf_type.get('ibo'):
                glDeleteBuffers(1, [buf_type['ibo']])