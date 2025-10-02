import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyrr import Matrix44
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from .cameraController import Camera

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
    
    # Vertex shader para gradientes
    VERTEX_SHADER_GRADIENT = """
    #version 330 core
    uniform mat4 mvp;
    layout(location = 0) in vec3 in_position;
    layout(location = 1) in float in_value;
    out float frag_value;
    void main() {
        gl_Position = mvp * vec4(in_position, 1.0);
        frag_value = in_value;
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
    
    # Fragment shader para gradientes
    FRAGMENT_SHADER_GRADIENT = """
    #version 330 core
    in float frag_value;
    out vec4 frag_color;
    
    uniform sampler1D colormap;
    uniform float value_min;
    uniform float value_max;
    
    void main() {
        float t = clamp((frag_value - value_min) / (value_max - value_min), 0.0, 1.0);
        frag_color = texture(colormap, t);
    }
    """
    
    FRAGMENT_SHADERS = {
        "solid": "out vec4 frag_color; void main() { frag_color = vec4(0.2, 0.2, 0.2, 1.0); }",
        "line": "out vec4 frag_color; void main() { frag_color = vec4(1.0, 0.2, 0.2, 1.0); }"
    }

    # Paletas de colores predefinidas
    COLOR_PALETTES = {
        "viridis": [
            (0.267004, 0.004874, 0.329415),
            (0.282623, 0.140926, 0.457517),
            (0.253935, 0.265254, 0.529983),
            (0.206756, 0.371758, 0.553117),
            (0.163625, 0.471133, 0.558148),
            (0.127568, 0.566949, 0.550556),
            (0.134692, 0.658636, 0.517649),
            (0.266941, 0.748751, 0.440573),
            (0.477504, 0.821444, 0.318195),
            (0.741388, 0.873449, 0.149561),
            (0.993248, 0.906157, 0.143936)
        ],
        "plasma": [
            (0.050383, 0.029803, 0.527975),
            (0.280264, 0.015654, 0.633301),
            (0.445680, 0.006352, 0.658034),
            (0.588235, 0.016658, 0.628050),
            (0.707188, 0.077863, 0.551710),
            (0.805257, 0.161158, 0.461497),
            (0.884850, 0.253522, 0.367040),
            (0.944006, 0.358379, 0.274460),
            (0.976853, 0.479434, 0.189503),
            (0.985673, 0.625984, 0.122738),
            (0.940015, 0.975158, 0.131326)
        ],
        "jet": [
            (0.0, 0.0, 0.5),
            (0.0, 0.0, 1.0),
            (0.0, 0.5, 1.0),
            (0.0, 1.0, 1.0),
            (0.5, 1.0, 0.5),
            (1.0, 1.0, 0.0),
            (1.0, 0.5, 0.0),
            (1.0, 0.0, 0.0),
            (0.5, 0.0, 0.0)
        ],
        "coolwarm": [
            (0.230, 0.299, 0.754),
            (0.706, 0.016, 0.150),
        ],
        "rainbow": [
            (0.5, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 1.0, 1.0),
            (0.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 0.0, 0.0)
        ],
        "grayscale": [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0)
        ]
    }

    def __init__(self, coords, triangle_indices, line_indices, parent=None):
        super().__init__(parent)

        self.coords_array = np.asarray(coords, dtype=np.float32)
        self.triangle_indices = np.asarray(triangle_indices, dtype=np.uint32)
        self.line_indices = np.asarray(line_indices, dtype=np.uint32)
        
        # Estado
        self.camera = None
        self.last_x, self.last_y = 0, 0
        self.current_mode = "solid"
        self.bg_color = (0.1, 0.1, 0.1)
        self.line_width = 1

        self.line_vertices_buffer = None
        
        # Estado de gradientes
        self.gradient_enabled = False
        self.node_values = None
        self.value_min = 0.0
        self.value_max = 1.0
        self.current_palette = "viridis"
        self.colormap_texture = None
        
        # Recursos OpenGL
        self.shader_programs = {}
        self.buffers = self._init_buffer_structure()
        
        # Flags
        self.gl_initialized = False
        
        self._setup_opengl_format()
    
    def _init_buffer_structure(self):
        """Inicializa la estructura de buffers"""
        return {
            'solid': {'vao': None, 'vbo': None, 'ibo': None, 'count': 0},
            'line': {'vao': None, 'vbo': None, 'count': 0},
            'gradient': {'vao': None, 'vbo_pos': None, 'vbo_val': None, 'ibo': None, 'count': 0}
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
        """Inicializa OpenGL"""
        print("Inicializando OpenGL...")
        
        # Configuración OpenGL básica
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_POLYGON_OFFSET_FILL)
        
        # Preparar buffer de líneas
        self._prepare_line_buffer()
        
        # Crear recursos OpenGL
        self._create_shaders()
        self._create_buffers()
        self._create_colormap_texture()
        self._setup_camera()
        
        self.gl_initialized = True
        print(f"Inicialización completa. Triángulos: {len(self.triangle_indices)//3}, Líneas: {len(self.line_indices)//2}")
    
    def _prepare_line_buffer(self):
        """Prepara el buffer de vértices para líneas"""
        self.line_vertices_buffer = np.zeros(len(self.line_indices) * 3, dtype=np.float32)
        self._update_line_vertices_buffer()
    
    def _update_line_vertices_buffer(self):
        """Actualiza el buffer de vértices de líneas basado en coordenadas actuales"""
        coords_flat = self.coords_array[self.line_indices].flatten()
        self.line_vertices_buffer[:] = coords_flat
    
    def _create_colormap_texture(self):
        """Crea la textura 1D para el mapa de colores"""
        self.colormap_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self.colormap_texture)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        self._update_colormap_texture()
    
    def _update_colormap_texture(self):
        """Actualiza la textura del mapa de colores con la paleta actual"""
        palette = self.COLOR_PALETTES.get(self.current_palette, self.COLOR_PALETTES["viridis"])
        
        # Interpolar la paleta a 256 colores
        num_colors = 256
        palette_array = np.array(palette, dtype=np.float32)
        
        # Crear interpolación
        t = np.linspace(0, 1, num_colors)
        palette_t = np.linspace(0, 1, len(palette))
        
        colors = np.zeros((num_colors, 3), dtype=np.float32)
        for i in range(3):  # R, G, B
            colors[:, i] = np.interp(t, palette_t, palette_array[:, i])
        
        # Subir a GPU
        glBindTexture(GL_TEXTURE_1D, self.colormap_texture)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGB32F, num_colors, 0, GL_RGB, GL_FLOAT, colors)
    
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
            
            # Shader de gradientes
            vs_grad = compileShader(self.VERTEX_SHADER_GRADIENT, GL_VERTEX_SHADER)
            fs_grad = compileShader(self.FRAGMENT_SHADER_GRADIENT, GL_FRAGMENT_SHADER)
            self.shader_programs["gradient"] = compileProgram(vs_grad, fs_grad)
            
            print("Shaders compilados exitosamente")
            
        except Exception as e:
            print(f"Error compilando shaders: {e}")
            raise
    
    def _create_buffers(self):
        """Crea todos los buffers OpenGL"""
        self._create_solid_buffers()
        self._create_line_buffers()
        self._create_gradient_buffers()
        glBindVertexArray(0)
        print("Buffers creados exitosamente")
    
    def _create_solid_buffers(self):
        """Crea buffers para renderizado sólido"""
        solid_buf = self.buffers['solid']
        solid_buf['vao'] = glGenVertexArrays(1)
        solid_buf['vbo'] = glGenBuffers(1)
        solid_buf['ibo'] = glGenBuffers(1)
        solid_buf['count'] = len(self.triangle_indices)
        
        glBindVertexArray(solid_buf['vao'])
        
        # VBO coordenadas
        glBindBuffer(GL_ARRAY_BUFFER, solid_buf['vbo'])
        glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # IBO índices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, solid_buf['ibo'])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangle_indices.nbytes, self.triangle_indices, GL_STATIC_DRAW)
    
    def _create_line_buffers(self):
        """Crea buffers para renderizado de líneas"""
        line_buf = self.buffers['line']
        line_buf['vao'] = glGenVertexArrays(1)
        line_buf['vbo'] = glGenBuffers(1)
        line_buf['count'] = len(self.line_indices)
        
        glBindVertexArray(line_buf['vao'])
        glBindBuffer(GL_ARRAY_BUFFER, line_buf['vbo'])
        glBufferData(GL_ARRAY_BUFFER, self.line_vertices_buffer.nbytes, self.line_vertices_buffer, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
    
    def _create_gradient_buffers(self):
        """Crea buffers para renderizado con gradientes"""
        grad_buf = self.buffers['gradient']
        grad_buf['vao'] = glGenVertexArrays(1)
        grad_buf['vbo_pos'] = glGenBuffers(1)
        grad_buf['vbo_val'] = glGenBuffers(1)
        grad_buf['ibo'] = glGenBuffers(1)
        grad_buf['count'] = len(self.triangle_indices)
        
        glBindVertexArray(grad_buf['vao'])
        
        # VBO coordenadas
        glBindBuffer(GL_ARRAY_BUFFER, grad_buf['vbo_pos'])
        glBufferData(GL_ARRAY_BUFFER, self.coords_array.nbytes, self.coords_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # VBO valores (inicialmente vacío)
        glBindBuffer(GL_ARRAY_BUFFER, grad_buf['vbo_val'])
        dummy_values = np.zeros(len(self.coords_array), dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, dummy_values.nbytes, dummy_values, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        
        # IBO índices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, grad_buf['ibo'])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangle_indices.nbytes, self.triangle_indices, GL_STATIC_DRAW)
    
    def _setup_camera(self):
        """Configura la cámara basada en el modelo"""
        model_center = self.coords_array.mean(axis=0)
        distances = np.linalg.norm(self.coords_array - model_center, axis=1)
        model_radius = max(distances.max() * 1.5, 1.0)
        self.camera = Camera(model_center, model_radius)
    
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
        
        elif shader_type == "gradient":
            # Configurar textura de colormap
            colormap_loc = glGetUniformLocation(shader, "colormap")
            if colormap_loc != -1:
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_1D, self.colormap_texture)
                glUniform1i(colormap_loc, 0)
            
            # Configurar rango de valores
            min_loc = glGetUniformLocation(shader, "value_min")
            max_loc = glGetUniformLocation(shader, "value_max")
            if min_loc != -1:
                glUniform1f(min_loc, self.value_min)
            if max_loc != -1:
                glUniform1f(max_loc, self.value_max)
    
    def _render_solid(self, mvp_matrix):
        """Renderiza el modelo sólido"""
        glPolygonOffset(1.0, 1.0)
        glEnable(GL_POLYGON_OFFSET_FILL)
        
        shader = self.shader_programs["solid"]
        glUseProgram(shader)
        self._set_shader_uniforms(shader, mvp_matrix, "solid")
        
        glBindVertexArray(self.buffers['solid']['vao'])
        glDrawElements(GL_TRIANGLES, self.buffers['solid']['count'], GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def _render_gradient(self, mvp_matrix):
        """Renderiza el modelo con gradientes"""
        if not self.gradient_enabled or self.node_values is None:
            self._render_solid(mvp_matrix)
            return
        
        glPolygonOffset(1.0, 1.0)
        glEnable(GL_POLYGON_OFFSET_FILL)
        
        shader = self.shader_programs["gradient"]
        glUseProgram(shader)
        self._set_shader_uniforms(shader, mvp_matrix, "gradient")
        
        glBindVertexArray(self.buffers['gradient']['vao'])
        glDrawElements(GL_TRIANGLES, self.buffers['gradient']['count'], GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def _render_wireframe(self, mvp_matrix):
        """Renderiza el modelo en alambre"""
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
        
        # Calcular matriz MVP
        mvp_matrix = self._calculate_mvp_matrix()
        
        # Renderizar según modo
        if self.current_mode == "solid":
            if self.gradient_enabled:
                self._render_gradient(mvp_matrix)
            else:
                self._render_solid(mvp_matrix)
        elif self.current_mode == "wireframe":
            self._render_wireframe(mvp_matrix)
        elif self.current_mode == "combined":
            if self.gradient_enabled:
                self._render_gradient(mvp_matrix)
            else:
                self._render_solid(mvp_matrix)
            glDepthMask(GL_FALSE)
            self._render_wireframe(mvp_matrix)
            glDepthMask(GL_TRUE)
    
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
    
    def set_node_values(self, values, auto_range=True):
        """
        Establece los valores nodales para el gradiente.
        
        Args:
            values: Array de valores, uno por cada nodo/vértice
            auto_range: Si True, calcula automáticamente min/max de los valores
        """
        values_array = np.asarray(values, dtype=np.float32)
        
        if len(values_array) != len(self.coords_array):
            print(f"Error: Se esperan {len(self.coords_array)} valores, se recibieron {len(values_array)}")
            return
        
        self.node_values = values_array
        
        if auto_range:
            self.value_min = float(np.min(values_array))
            self.value_max = float(np.max(values_array))
            # Evitar división por cero
            if abs(self.value_max - self.value_min) < 1e-10:
                self.value_max = self.value_min + 1.0
        
        # Actualizar buffer de valores
        if self.gl_initialized:
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers['gradient']['vbo_val'])
            glBufferSubData(GL_ARRAY_BUFFER, 0, values_array.nbytes, values_array)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        print(f"Valores nodales actualizados. Rango: [{self.value_min:.3f}, {self.value_max:.3f}]")
        self.update()
    
    def set_value_range(self, min_val, max_val):
        """Establece manualmente el rango de valores para el gradiente"""
        self.value_min = float(min_val)
        self.value_max = float(max_val)
        if abs(self.value_max - self.value_min) < 1e-10:
            self.value_max = self.value_min + 1.0
        self.update()
    
    def set_color_palette(self, palette_name):
        """
        Cambia la paleta de colores.
        
        Args:
            palette_name: Nombre de la paleta ('viridis', 'plasma', 'jet', 'coolwarm', 'rainbow', 'grayscale')
        """
        if palette_name in self.COLOR_PALETTES:
            self.current_palette = palette_name
            if self.gl_initialized:
                self._update_colormap_texture()
            print(f"Paleta cambiada a: {palette_name}")
            self.update()
        else:
            print(f"Paleta '{palette_name}' no encontrada. Disponibles: {list(self.COLOR_PALETTES.keys())}")
    
    def enable_gradient(self, enabled=True):
        """Habilita o deshabilita el renderizado con gradientes"""
        self.gradient_enabled = enabled
        self.update()
    
    def is_gradient_enabled(self):
        """Retorna si el gradiente está habilitado"""
        return self.gradient_enabled
    
    def get_available_palettes(self):
        """Retorna la lista de paletas disponibles"""
        return list(self.COLOR_PALETTES.keys())
    
    def update_coords(self, new_coords):
        """Actualiza solo las coordenadas de los vértices - OPTIMIZADO"""
        new_coords_array = np.asarray(new_coords, dtype=np.float32)
        if new_coords_array.shape != self.coords_array.shape:
            print(f"Error: Las nuevas coordenadas deben tener la misma forma que las originales")
            print(f"Original: {self.coords_array.shape}, Nueva: {new_coords_array.shape}")
            return
        
        # Actualizar coordenadas
        self.coords_array[:] = new_coords_array
        
        if self.gl_initialized:
            # Actualizar buffer sólido
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers['solid']['vbo'])
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.coords_array.nbytes, self.coords_array)
            
            # Actualizar buffer de gradientes
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers['gradient']['vbo_pos'])
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.coords_array.nbytes, self.coords_array)
            
            # Actualizar buffer de líneas
            self._update_line_vertices_buffer()
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers['line']['vbo'])
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.line_vertices_buffer.nbytes, self.line_vertices_buffer)
            
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            self.update()
    
    def update_camera_for_current_model(self):
        """Recalcula la cámara para el modelo actual"""
        if self.gl_initialized:
            self._setup_camera()
            self.update()
    
    def __del__(self):
        """Limpieza de recursos OpenGL"""
        if hasattr(self, 'buffers') and self.gl_initialized:
            self._cleanup_opengl_resources()
    
    def _cleanup_opengl_resources(self):
        """Limpia los recursos OpenGL"""
        try:
            for buf_type in self.buffers.values():
                if buf_type.get('vao'):
                    glDeleteVertexArrays(1, [buf_type['vao']])
                if buf_type.get('vbo'):
                    glDeleteBuffers(1, [buf_type['vbo']])
                if buf_type.get('vbo_pos'):
                    glDeleteBuffers(1, [buf_type['vbo_pos']])
                if buf_type.get('vbo_val'):
                    glDeleteBuffers(1, [buf_type['vbo_val']])
                if buf_type.get('ibo'):
                    glDeleteBuffers(1, [buf_type['ibo']])
            
            if self.colormap_texture:
                glDeleteTextures(1, [self.colormap_texture])
        except:
            pass