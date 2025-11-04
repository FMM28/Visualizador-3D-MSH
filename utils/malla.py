import numpy as np
from collections import Counter

def filtrar_elementos_visibles(coords, elements):
    """
    Filtra elementos para renderizar solo la superficie externa.
    """
    
    coords_array = np.asarray(coords, dtype=np.float32)
    
    # Detectar tipo de geometria
    n_nodes = len(elements[0])
    
    # Caso 2D Triangulos
    if n_nodes == 3:
        triangles_array = np.array(elements, dtype=np.int32)
        surface_nodes = np.unique(triangles_array.flatten())
        
        # Crear mapeo
        node_map_array = np.full(coords_array.shape[0], -1, dtype=np.int32)
        node_map_array[surface_nodes] = np.arange(len(surface_nodes), dtype=np.int32)
        
        # Reindexar
        coords_surface = coords_array[surface_nodes]
        triangles_reindexed = node_map_array[triangles_array]
        triangle_indices = triangles_reindexed.flatten().astype(np.uint32)
        
        # Extraer aristas
        edges = np.concatenate([
            triangles_reindexed[:, [0, 1]],
            triangles_reindexed[:, [1, 2]],
            triangles_reindexed[:, [2, 0]]
        ], axis=0)
        
        edges_sorted = np.sort(edges, axis=1)
        edges_complex = edges_sorted[:, 0] + 1j * edges_sorted[:, 1]
        _, unique_indices = np.unique(edges_complex, return_index=True)
        line_indices = edges_sorted[unique_indices].flatten().astype(np.uint32)
        
        node_map = {int(old_idx): int(new_idx) for new_idx, old_idx in enumerate(surface_nodes)}
        return coords_surface, triangle_indices, line_indices, node_map
    
    # Caso 3D Tetraedros
    elif n_nodes == 4:
        TETRA_FACES = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.int32)
        
        tetra_array = np.array(elements, dtype=np.int32)
        
        # Generar todas las caras vectorizadamente
        all_faces = tetra_array[:, TETRA_FACES]
        all_faces = all_faces.reshape(-1, 3)
        
        # Ordenar
        faces_sorted = np.sort(all_faces, axis=1)
        
        # Contar caras usando Counter
        faces_tuples = [tuple(face) for face in faces_sorted]
        face_counts = Counter(faces_tuples)
        
        # Extraer solo caras externas
        external_faces = [all_faces[i] for i, face_tuple in enumerate(faces_tuples) 
                         if face_counts[face_tuple] == 1]
        
        triangles_array = np.array(external_faces, dtype=np.int32)
        surface_nodes = np.unique(triangles_array.flatten())
        
        # Crear mapeo
        node_map_array = np.full(coords_array.shape[0], -1, dtype=np.int32)
        node_map_array[surface_nodes] = np.arange(len(surface_nodes), dtype=np.int32)
        
        # Reindexar
        coords_surface = coords_array[surface_nodes]
        triangles_reindexed = node_map_array[triangles_array]
        triangle_indices = triangles_reindexed.flatten().astype(np.uint32)
        
        # Extraer aristas
        edges = np.concatenate([
            triangles_reindexed[:, [0, 1]],
            triangles_reindexed[:, [1, 2]],
            triangles_reindexed[:, [2, 0]]
        ], axis=0)
        
        edges_sorted = np.sort(edges, axis=1)
        edges_complex = edges_sorted[:, 0] + 1j * edges_sorted[:, 1]
        _, unique_indices = np.unique(edges_complex, return_index=True)
        line_indices = edges_sorted[unique_indices].flatten().astype(np.uint32)
        
        node_map = {int(old_idx): int(new_idx) for new_idx, old_idx in enumerate(surface_nodes)}
        return coords_surface, triangle_indices, line_indices, node_map
    
    else:
        raise ValueError(f"Tipo de elemento no soportado: {n_nodes} nodos")

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