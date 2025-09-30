import numpy as np

def flatten(coords, elements):
    """
    Aplana coordenadas y elementos para OpenGL.
    """
    coords_array = np.asarray(coords, dtype=np.float32)

    elements_int = [np.array(elem, dtype=np.int32) for elem in elements]
    triangles_list = []
    edges_set = set()

    TETRA_FACES = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.int32)
    
    for elem in elements_int:
        n_nodes = len(elem)
        
        if n_nodes == 3: # Triángulo
            triangles_list.append(elem)
            edges_set.add(tuple(sorted((elem[0], elem[1]))))
            edges_set.add(tuple(sorted((elem[1], elem[2]))))
            edges_set.add(tuple(sorted((elem[2], elem[0]))))

        elif n_nodes == 4: # Tetraedro
            for face in TETRA_FACES:
                triangle = elem[face]
                triangles_list.append(triangle)
                edges_set.add(tuple(sorted((triangle[0], triangle[1]))))
                edges_set.add(tuple(sorted((triangle[1], triangle[2]))))
                edges_set.add(tuple(sorted((triangle[2], triangle[0]))))
    
    triangle_indices = np.array(triangles_list, dtype=np.uint32).flatten()
    line_indices = np.array(list(edges_set), dtype=np.uint32).flatten()
    
    return coords_array, triangle_indices, line_indices