import os

import meshio
import numpy as np


class Lector:
    def __init__(self):
        self.carpeta = None
        self.archivos_vtu = []
        self.total_modelos = 0

    def abrir_carpeta(self, carpeta):
        self.carpeta = carpeta
        if not os.path.exists(carpeta):
            raise FileNotFoundError(f"La carpeta {carpeta} no existe")

        self.archivos_vtu = sorted(
            [f for f in os.listdir(carpeta) if f.lower().endswith('.vtu')]
        )
        self.total_modelos = len(self.archivos_vtu)

        if self.total_modelos == 0:
            print("Advertencia: No se encontraron archivos .vtu en la carpeta.")
        else:
            print(f"Total de modelos cargados: {self.total_modelos}")

    def _leer_vtu(self, vtu_file):
        """Lee el archivo VTU una sola vez (ASCII, binario o comprimido)."""
        ruta = os.path.join(self.carpeta, vtu_file)
        try:
            return meshio.read(ruta, file_format="vtu")
        except Exception as e:
            print(f"Error al leer {vtu_file}: {e}")
            return None

    def _extraer_msh(self, malla):

        if malla is None:
            return np.array([]), np.array([])

        coordenadas = np.asarray(malla.points, dtype=np.float64)
        if coordenadas.size and coordenadas.shape[1] == 2:  # 2D añadir z = 0
            coordenadas = np.hstack([coordenadas, np.zeros((len(coordenadas), 1))])

        elementos_lista = []
        for bloque in malla.cells:  # se concatenan en el orden del archivo
            elementos_lista.extend(list(map(int, fila)) for fila in bloque.data)

        elementos = np.empty(len(elementos_lista), dtype=object)
        for k, nodos in enumerate(elementos_lista):
            elementos[k] = nodos
        return coordenadas, elementos

    @staticmethod
    def _crear_entrada(nombre, tipo, valores, con_ids=True):
        valores = np.asarray(valores)
        entrada = {
            "nombre": nombre,
            "tipo": tipo,  # "point_data" | "cell_data" | "field_data"
            "ids": np.arange(1, len(valores) + 1, dtype=np.int32) if (con_ids and valores.ndim > 0) else None,
            "valores": valores,
            "componentes": 1 if valores.ndim <= 1 else int(np.prod(valores.shape[1:])),
            "forma": valores.shape,
            "dtype": str(valores.dtype),
        }
        return entrada

    def _extraer_res(self, malla):

        resultados = {}
        if malla is None:
            return resultados

        def agregar(entrada):
            clave = entrada["nombre"]
            if clave in resultados:
                clave = f'{entrada["nombre"]}@{entrada["tipo"]}'
            resultados[clave] = entrada

        for nombre, valores in malla.point_data.items():
            agregar(self._crear_entrada(nombre, "point_data", valores))

        for nombre, bloques in malla.cell_data.items():
            valores = np.concatenate([np.asarray(b) for b in bloques])
            agregar(self._crear_entrada(nombre, "cell_data", valores))

        for nombre, valores in (malla.field_data or {}).items():
            agregar(self._crear_entrada(nombre, "field_data", valores, con_ids=False))

        return resultados

    def obtener_modelo(self, indice):
        vtu_file = self.archivos_vtu[indice]
        malla = self._leer_vtu(vtu_file)  # una sola lectura para malla y resultados
        return {
            "msh": self._extraer_msh(malla),
            "res": self._extraer_res(malla)
        }

    def obtener_nombre_modelo(self, indice):
        return self.archivos_vtu[indice]

    def __str__(self):
        status = [
            f"Carpeta: {self.carpeta}",
            f"Total de modelos: {self.total_modelos}"
        ]
        if self.total_modelos > 0:
            status.append("Modelos:")
            for i, vtu in enumerate(self.archivos_vtu):
                status.append(f"  [{i}] {vtu}")
        return "\n".join(status)