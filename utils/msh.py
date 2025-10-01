import os
import numpy as np

class Lector:
    def __init__(self):
        self.carpeta = None
        self.archivos_msh = []
        self.total_modelos = 0

    def abrir_carpeta(self, carpeta):
        self.carpeta = carpeta
        if not os.path.exists(carpeta):
            raise FileNotFoundError(f"La carpeta {carpeta} no existe")

        self.archivos_msh = sorted([f for f in os.listdir(carpeta) if f.lower().endswith('.msh')])
        self.total_modelos = len(self.archivos_msh)

        if self.total_modelos == 0:
            print("Advertencia: No se encontraron archivos .msh en la carpeta.")
        else:
            print(f"Total de modelos cargados: {self.total_modelos}")

    def _leer_msh(self, msh_file):
        ruta = os.path.join(self.carpeta, msh_file)
        
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
        except Exception as e:
            print(f"Error al leer {msh_file}: {e}")
            return np.array([]), np.array([])

        coordenadas_lista = []
        elementos_lista = []

        i = 0
        while i < len(lineas):
            linea = lineas[i].strip().lower()

            # Coordenadas
            if linea.startswith("coordinates"):
                i += 1
                while i < len(lineas):
                    l_clean = lineas[i].strip().lower()
                    if l_clean.startswith("end coordinates"):
                        break
                    partes = lineas[i].split()
                    if len(partes) >= 3:
                        try:
                            if len(partes) == 4:  # 3D
                                coords = list(map(float, partes[1:4]))
                            elif len(partes) == 3:  # 2D
                                coords = list(map(float, partes[1:3]))
                                coords.append(0.0)
                            else:
                                i += 1
                                continue
                            coordenadas_lista.append(coords)
                        except ValueError:
                            pass
                    i += 1

            # Elementos
            elif linea.startswith("elements"):
                i += 1
                while i < len(lineas):
                    l_clean = lineas[i].strip().lower()
                    if l_clean.startswith("end elements"):
                        break
                    partes = lineas[i].split()
                    if len(partes) >= 4:
                        try:
                            nodos = [int(idx) - 1 for idx in partes[1:-1]]
                            elementos_lista.append(nodos)
                        except ValueError:
                            pass
                    i += 1
            else:
                i += 1

        coordenadas = np.array(coordenadas_lista, dtype=np.float64) if coordenadas_lista else np.array([])
        elementos = np.array(elementos_lista, dtype=object) if elementos_lista else np.array([])
        
        return coordenadas, elementos

    def _leer_res(self, res_file):
        ruta = os.path.join(self.carpeta, res_file)
        if not os.path.exists(ruta):
            print(f"Archivo .res no encontrado: {ruta}")
            return {
                "desplazamientos": None,
                "esfuerzos_nodos": None,
                "esfuerzos_gauss": None
            }

        try:
            with open(ruta, 'r', encoding='iso-8859-1') as f:
                lineas = f.readlines()
        except Exception as e:
            print(f"Error al leer {res_file}: {e}")
            return {
                "desplazamientos": None,
                "esfuerzos_nodos": None,
                "esfuerzos_gauss": None
            }

        datos = {
            "desplazamientos": None,
            "esfuerzos_nodos": None,
            "esfuerzos_gauss": None
        }

        seccion_actual = None
        valores_actuales = []
        ids_actuales = []
        tipo_actual = None

        for i, linea in enumerate(lineas):
            linea_clean = linea.strip().lower()

            # Detectar inicio de sección
            if 'result' in linea_clean:
                if 'desplazamientos' in linea_clean:
                    tipo_actual = "desplazamientos"
                    seccion_actual = "values"
                    valores_actuales = []
                    ids_actuales = []
                elif 'esfuerzo' in linea_clean and 'gauss' not in linea_clean:
                    tipo_actual = "esfuerzos_nodos"
                    seccion_actual = "values"
                    valores_actuales = []
                    ids_actuales = []
                elif 'gauss' in linea_clean:
                    tipo_actual = "esfuerzos_gauss"
                    seccion_actual = "values"
                    valores_actuales = []
                    ids_actuales = []
                continue

            # Detectar inicio de bloque values
            if linea_clean.startswith("values"):
                seccion_actual = "values"
                continue

            # Detectar fin de bloque values
            if linea_clean.startswith("end values"):
                if tipo_actual and valores_actuales:
                    if tipo_actual == "desplazamientos":
                        desplazamientos_procesados = []
                        for val in valores_actuales:
                            if len(val) == 3:
                                desplazamientos_procesados.append(val)
                            elif len(val) == 4:
                                desplazamientos_procesados.append(val[1:])
                        if desplazamientos_procesados:
                            datos[tipo_actual] = (np.array(ids_actuales, dtype=np.int32), 
                                                 np.array(desplazamientos_procesados, dtype=np.float64))
                    else:
                        datos[tipo_actual] = (np.array(ids_actuales, dtype=np.int32), 
                                             np.array(valores_actuales, dtype=np.float64))
                
                # Resetear para la próxima sección
                seccion_actual = None
                tipo_actual = None
                valores_actuales = []
                ids_actuales = []
                continue

            # Procesar líneas de datos dentro de la sección values
            if seccion_actual == "values" and linea_clean and linea_clean[0].isdigit():
                partes = linea_clean.split()
                try:
                    id_val = int(partes[0])
                    if tipo_actual == "desplazamientos":
                        if len(partes) == 4:
                            valores = list(map(float, partes[1:4]))
                        elif len(partes) == 3:
                            valores = list(map(float, partes[1:3]))
                            valores.append(0.0)
                        else:
                            continue
                    else:
                        valores = list(map(float, partes[1:]))
                    
                    ids_actuales.append(id_val)
                    valores_actuales.append(valores)
                    
                except (ValueError, IndexError):
                    continue

        return datos

    def obtener_modelo(self, indice):
        msh_file = self.archivos_msh[indice]
        res_file = msh_file.rsplit('.', 1)[0] + '.RES'
        datos = {
            "msh": self._leer_msh(msh_file),
            "res": self._leer_res(res_file)
        }
        return datos

    def obtener_nombre_modelo(self, indice):
        return self.archivos_msh[indice]

    def __str__(self):
        status = [
            f"Carpeta: {self.carpeta}",
            f"Total de modelos: {self.total_modelos}"
        ]
        if self.total_modelos > 0:
            status.append("Modelos:")
            for i, msh in enumerate(self.archivos_msh):
                status.append(f"  [{i}] {msh}")
        return "\n".join(status)