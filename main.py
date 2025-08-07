from msh import LectorMsh
import glfw
import moderngl
import numpy as np
from pyrr import Matrix44,Vector3

lector = LectorMsh()

lector.abrir_carpeta(r'C:\Users\frank\Downloads\Para Visualizaciones\Para Visualizaciones\3D')
# C:\Users\frank\Downloads\Para Visualizaciones\Para Visualizaciones\2D\Agrietamiento
# C:\Users\frank\Downloads\Para Visualizaciones\Para Visualizaciones\3D
print("Total de modelos:", lector.total_modelos)

lector.ir_al_ultimo()
coords, elements = lector.obtener_modelo_actual()

class Camera:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.reset()
        
    def reset(self):
        self.distance = self.radius * 2.5
        self.rotation_x = 0.0  # Rotación vertical (radianes)
        self.rotation_y = 0.0  # Rotación horizontal (radianes)
        self.pan_x = 0.0       # Traslación horizontal
        self.pan_y = 0.0       # Traslación vertical
        self.zoom_speed = 0.1
        self.rotation_speed = 0.01
        self.pan_speed = 0.005
        
    def get_view_matrix(self):
        # Calcular posición de la cámara
        eye = Vector3([
            self.distance * np.cos(self.rotation_y) * np.cos(self.rotation_x),
            self.distance * np.sin(self.rotation_x),
            self.distance * np.sin(self.rotation_y) * np.cos(self.rotation_x)
        ])
        
        # Aplicar traslación
        target = Vector3([
            self.center[0] + self.pan_x,
            self.center[1] + self.pan_y,
            self.center[2]
        ])
        
        return Matrix44.look_at(
            eye.xyz + target.xyz,  # Posición del ojo
            target.xyz,            # Punto de mira
            (0.0, 1.0, 0.0)        # Vector arriba
        )
    
    def rotate(self, dx, dy):
        self.rotation_y += dx * self.rotation_speed
        self.rotation_x += dy * self.rotation_speed
        # Limitar rotación vertical para evitar voltear
        self.rotation_x = np.clip(self.rotation_x, -np.pi/2 + 0.01, np.pi/2 - 0.01)
    
    def pan(self, dx, dy):
        self.pan_x += dx * self.pan_speed * self.distance
        self.pan_y += dy * self.pan_speed * self.distance
    
    def zoom(self, amount):
        self.distance *= 1.0 - amount * self.zoom_speed
        # Limitar distancia mínima y máxima
        self.distance = np.clip(self.distance, self.radius * 0.5, self.radius * 10.0)

def main():
    # ========================================================================
    # 1. Datos de entrada (personalizar con tus datos)
    # ========================================================================
    # Ejemplo simple de un tetraedro
    
    # ========================================================================
    # 2. Procesamiento de datos para aristas
    # ========================================================================
    coords_3d = []
    for point in coords:
        if len(point) == 2:
            coords_3d.append([point[0], point[1], 0.0])
        else:
            coords_3d.append(point)
    
    coords_array = np.array(coords_3d, dtype='f4')
    
    # Generar aristas para tetraedros
    edges = []
    
    for elem in elements:
        idxs = [i - 1 for i in elem]  # Convertir a base-0
        
        # Para tetraedros (4 vértices)
        if len(idxs) == 4:
            # Todas las combinaciones de aristas en un tetraedro (6 aristas)
            edges.append([idxs[0], idxs[1]])
            edges.append([idxs[0], idxs[2]])
            edges.append([idxs[0], idxs[3]])
            edges.append([idxs[1], idxs[2]])
            edges.append([idxs[1], idxs[3]])
            edges.append([idxs[2], idxs[3]])
    
    edges_array = np.array(edges, dtype='i4')
    
    # ========================================================================
    # 3. Configuración de OpenGL - RENDERIZADO DE ARISTAS
    # ========================================================================
    if not glfw.init():
        return
    
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    
    window = glfw.create_window(1200, 800, "Visualización de Aristas de Tetraedros", None, None)
    if not window:
        glfw.terminate()
        return
    
    glfw.make_context_current(window)
    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST)
    
    # Shaders para renderizado de líneas
    vert_shader = """
    #version 330 core
    uniform mat4 mvp;
    in vec3 in_position;
    void main() {
        gl_Position = mvp * vec4(in_position, 1.0);
    }
    """
    
    frag_shader = """
    #version 330 core
    out vec4 frag_color;
    void main() {
        // Color rojo para las aristas
        frag_color = vec4(0.9, 0.1, 0.1, 1.0);
    }
    """
    
    prog = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
    mvp = prog['mvp']
    
    # Crear buffers
    vbo = ctx.buffer(coords_array.tobytes())
    ibo = ctx.buffer(edges_array.tobytes())
    
    vao = ctx.vertex_array(
        prog,
        [(vbo, '3f', 'in_position')],
        index_buffer=ibo,
        index_element_size=4
    )
    
    # Configurar cámara
    center = np.array(coords_array.mean(axis=0))
    radius = np.linalg.norm(coords_array - center, axis=1).max() * 2.0
    camera = Camera(center, radius)
    
    # Variables para control del ratón
    last_x, last_y = 0, 0
    mouse_pressed = {'left': False, 'right': False}
    
    # Callbacks para el ratón
    def mouse_button_callback(window, button, action, mods):
        nonlocal last_x, last_y
        if button == glfw.MOUSE_BUTTON_LEFT:
            mouse_pressed['left'] = (action == glfw.PRESS)
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            mouse_pressed['right'] = (action == glfw.PRESS)
        
        if action == glfw.PRESS:
            last_x, last_y = glfw.get_cursor_pos(window)
    
    def cursor_pos_callback(window, x, y):
        nonlocal last_x, last_y
        dx, dy = x - last_x, y - last_y
        last_x, last_y = x, y
        
        if mouse_pressed['left']:
            camera.rotate(dx, dy)
        elif mouse_pressed['right']:
            camera.pan(dx, dy)
    
    def scroll_callback(window, dx, dy):
        camera.zoom(dy)
    
    # Registrar callbacks
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    
    # ========================================================================
    # 4. Bucle principal de renderizado
    # ========================================================================
    while not glfw.window_should_close(window):
        glfw.poll_events()
        
        # Actualizar cámara
        width, height = glfw.get_window_size(window)
        ratio = width / height
        
        # Calcular matrices
        view = camera.get_view_matrix()
        proj = Matrix44.perspective_projection(45.0, ratio, 0.1, camera.radius * 10)
        mvp_val = (proj * view).astype('f4')
        
        # Actualizar uniformes
        mvp.write(mvp_val.tobytes())
        
        # Renderizar
        ctx.clear(1.0, 1.0, 1.0)  # Fondo blanco
        
        # Grosor de las líneas
        ctx.line_width = 2.5
        
        # Renderizar aristas como líneas
        vao.render(moderngl.LINES)
        
        glfw.swap_buffers(window)
    
    glfw.terminate()

if __name__ == '__main__':
    main()