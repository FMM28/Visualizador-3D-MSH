import numpy as np
from collections import defaultdict

def filtrar_elementos_visibles(coords, elements):
    """
    Filtra elementos para renderizar solo la superficie externa.
    """
    
    TETRA_FACES = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.int32)
    
    coords_array = np.asarray(coords, dtype=np.float32)
    elements_int = [np.array(elem, dtype=np.int32) for elem in elements]

    # Contador de caras: si una cara aparece 1 vez, es externa
    face_count = defaultdict(int)
    face_to_nodes = {}
    
    triangles_surface = []
    
    for elem in elements_int:
        n_nodes = len(elem)
        
        if n_nodes == 3:    # Triángulo
            triangles_surface.append(elem)
            
        elif n_nodes == 4:  # Tetraedro
            for face_def in TETRA_FACES:
                face_nodes = elem[face_def]
                canonical_face = tuple(sorted(face_nodes))
                face_count[canonical_face] += 1
                face_to_nodes[canonical_face] = face_nodes
    
    for canonical_face, count in face_count.items():
        if count == 1:  # Cara externa
            triangles_surface.append(face_to_nodes[canonical_face])
    
    if len(triangles_surface) == 0:
        print("Advertencia: No se encontraron triángulos de superficie")
        return coords_array, np.array([], dtype=np.uint32), np.array([], dtype=np.uint32), {}
    
    # Identificar nodos únicos en la superficie
    surface_nodes = set()
    for tri in triangles_surface:
        surface_nodes.update(tri)
    
    # Mapear índices originales a nuevos
    surface_nodes_sorted = sorted(surface_nodes)
    node_map = {old_idx: new_idx for new_idx, old_idx in enumerate(surface_nodes_sorted)}
    
    # Reindexar coordenadas
    coords_surface = coords_array[surface_nodes_sorted]
    
    # Reindexar triángulos
    triangles_reindexed = []
    edges_set = set()
    
    for tri in triangles_surface:
        new_tri = [node_map[node] for node in tri]
        triangles_reindexed.append(new_tri)
        
        # Extraer aristas
        edges_set.add(tuple(sorted((new_tri[0], new_tri[1]))))
        edges_set.add(tuple(sorted((new_tri[1], new_tri[2]))))
        edges_set.add(tuple(sorted((new_tri[2], new_tri[0]))))
    
    triangle_indices = np.array(triangles_reindexed, dtype=np.uint32).flatten()
    line_indices = np.array(list(edges_set), dtype=np.uint32).flatten()
    
    return coords_surface, triangle_indices, line_indices, node_map

def mapear_nodos(nodos, node_map):
    """
    Mapea los nodos originales a nodos visibles.
    """
    
    node_ids, disp_values = nodos

    disp_dict = {}
    for i, node_id in enumerate(node_ids):
        disp_dict[node_id] = disp_values[i]
    
    num_visible_nodes = len(node_map)
    disp_array = np.zeros((num_visible_nodes, 3), dtype=np.float64)
    
    for old_idx, new_idx in node_map.items():
        node_id = old_idx + 1
        
        if node_id in disp_dict:
            disp_array[new_idx] = disp_dict[node_id]
    
    return disp_array