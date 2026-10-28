import numpy as np

TETRA_FACES = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.int32)


def _caras_externas(all_faces):
    """Máscara booleana de las caras que aparecen una sola vez."""
    faces_sorted = np.sort(all_faces, axis=1)
    order = np.lexsort((faces_sorted[:, 2], faces_sorted[:, 1], faces_sorted[:, 0]))
    fs = faces_sorted[order]

    nuevo_grupo = np.empty(len(fs), dtype=bool)
    nuevo_grupo[0] = True
    nuevo_grupo[1:] = np.any(fs[1:] != fs[:-1], axis=1)

    group_id = np.cumsum(nuevo_grupo) - 1
    counts = np.bincount(group_id)

    mask = np.empty(len(fs), dtype=bool)
    mask[order] = counts[group_id] == 1
    return mask


def _reindexar_superficie(coords_array, triangles_array):
    surface_nodes = np.unique(triangles_array)

    node_map_array = np.full(coords_array.shape[0], -1, dtype=np.int32)
    node_map_array[surface_nodes] = np.arange(len(surface_nodes), dtype=np.int32)

    coords_surface = coords_array[surface_nodes]
    triangles_reindexed = node_map_array[triangles_array]
    triangle_indices = triangles_reindexed.ravel().astype(np.uint32)

    edges = np.concatenate([
        triangles_reindexed[:, [0, 1]],
        triangles_reindexed[:, [1, 2]],
        triangles_reindexed[:, [2, 0]],
    ], axis=0)
    edges_sorted = np.sort(edges, axis=1)
    edges_key = edges_sorted[:, 0].astype(np.int64) * len(surface_nodes) + edges_sorted[:, 1]
    _, unique_indices = np.unique(edges_key, return_index=True)
    line_indices = edges_sorted[unique_indices].ravel().astype(np.uint32)

    return coords_surface, triangle_indices, line_indices, surface_nodes


def _elementos_a_array(elements):
    elements = list(elements)
    if len(elements) == 0:
        raise ValueError("La malla no tiene elementos")

    longitudes = np.fromiter((len(e) for e in elements), dtype=np.int32, count=len(elements))
    if (longitudes == 4).any():
        n_nodes = 4
    elif (longitudes == 3).any():
        n_nodes = 3
    else:
        raise ValueError(f"Tipo de elemento no soportado: longitudes {np.unique(longitudes)}")

    elem_ids = np.flatnonzero(longitudes == n_nodes).astype(np.int32)
    arr = np.array([elements[i] for i in elem_ids], dtype=np.int32)
    return arr, elem_ids


def filtrar_elementos_visibles(coords, elements):
    """
    Filtra los elementos de la malla para quedarse solo con los que son visibles.
    """
    coords_array = np.asarray(coords, dtype=np.float32)
    elements_array, elem_ids = _elementos_a_array(elements)
    n_nodes = elements_array.shape[1]

    if n_nodes == 3:
        triangles_array = elements_array
        tri_to_elem = elem_ids

    else:  # 4 nodos
        all_faces = elements_array[:, TETRA_FACES].reshape(-1, 3)
        mask = _caras_externas(all_faces)
        triangles_array = all_faces[mask]
        tri_to_elem = elem_ids[np.flatnonzero(mask) // 4]

    coords_surface, triangle_indices, line_indices, surface_nodes = _reindexar_superficie(
        coords_array, triangles_array
    )
    return coords_surface, triangle_indices, line_indices, surface_nodes, tri_to_elem.astype(np.int32)


def mapear_datos(ids, values, target_ids, fill=0.0):
    """
    Mapea datos de un conjunto de IDs a otro conjunto de IDs.
    """
    ids = np.asarray(ids, dtype=np.int64)
    values = np.asarray(values, dtype=np.float64)
    target_ids = np.asarray(target_ids, dtype=np.int64)

    max_id = max(ids.max(), target_ids.max())
    lookup = np.full((max_id + 1,) + values.shape[1:], fill, dtype=np.float64)
    lookup[ids] = values
    return lookup[target_ids]


def reindexar_resultados(res, surface_nodes, tri_to_elem, fill=0.0):
    """
    Reindexa los resultados del lector a la geometría de superficie:
      - point_data -> un valor por nodo de coords_surface
      - cell_data  -> un valor por triángulo (hereda el valor de su elemento)
      - field_data -> se omite
    Las entradas devueltas mantienen nombre/tipo; 'ids' pasa a ser el ID original
    (base 1) del nodo o elemento de cada fila, y 'valores' queda alineado por
    posición con los vértices o triángulos renderizados.
    """
    nodos_ids = np.asarray(surface_nodes, dtype=np.int64) + 1
    tri_ids = np.asarray(tri_to_elem, dtype=np.int64) + 1

    salida = {}
    for clave, r in res.items():
        if r["tipo"] == "point_data":
            target = nodos_ids
        elif r["tipo"] == "cell_data":
            target = tri_ids
        else:
            continue

        if not np.issubdtype(np.asarray(r["valores"]).dtype, np.number):
            continue

        valores = mapear_datos(r["ids"], r["valores"], target, fill)
        nuevo = dict(r)
        nuevo["ids"] = target
        nuevo["valores"] = valores
        nuevo["forma"] = valores.shape
        nuevo["dtype"] = str(valores.dtype)
        salida[clave] = nuevo
    return salida