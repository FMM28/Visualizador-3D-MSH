import os

class LectorMsh:
    def __init__(self):
        self.carpeta = None
        self.archivos = []
        self.total_modelos = 0
        self.indice_actual = -1

    def abrir_carpeta(self, carpeta):
        """Abre la carpeta y lista todos los archivos .msh"""
        self.carpeta = carpeta
        self.archivos = sorted([
            f for f in os.listdir(carpeta) if f.lower().endswith('.msh')
        ])
        self.total_modelos = len(self.archivos)
        self.indice_actual = -1

    def _leer_archivo(self, indice):
        """Lee y devuelve coordenadas y elementos de un archivo .msh"""
        if indice < 0 or indice >= self.total_modelos:
            return None, None

        ruta = os.path.join(self.carpeta, self.archivos[indice])
        coordenadas = []
        elementos = []

        with open(ruta, 'r') as f:
            lineas = f.readlines()

        i = 0
        while i < len(lineas):
            linea = lineas[i].strip().lower()

            if linea.startswith("coordinates"):
                i += 1
                while i < len(lineas):
                    linea = lineas[i].strip().lower()
                    if linea.startswith("end coordinates"):
                        break
                    partes = lineas[i].split()
                    if len(partes) >= 3:
                        coords = list(map(float, partes[1:]))
                        coordenadas.append(coords)
                    i += 1

            elif linea.startswith("elements"):
                i += 1
                while i < len(lineas):
                    linea = lineas[i].strip().lower()
                    if linea.startswith("end elements"):
                        break
                    partes = lineas[i].split()
                    if len(partes) >= 4:
                        nodos = [int(idx) - 1 for idx in partes[1:-1]]
                        elementos.append(nodos)
                    i += 1
            else:
                i += 1

        return coordenadas, elementos

    def ir_a(self, indice):
        """Va al modelo con el índice especificado"""
        if not (0 <= indice < self.total_modelos):
            return False

        self.indice_actual = indice
        print(f"Cargado: {self.obtener_nombre_actual()}")
        return True

    def ir_al_primero(self):
        return self.ir_a(0)

    def ir_al_ultimo(self):
        return self.ir_a(self.total_modelos - 1)

    def obtener_modelo_actual(self):
        """Devuelve coordenadas y elementos del modelo actual"""
        if self.indice_actual == -1:
            return None, None
        return self._leer_archivo(self.indice_actual)

    def obtener_nombre_actual(self):
        """Devuelve el nombre del archivo actual"""
        if 0 <= self.indice_actual < self.total_modelos:
            return self.archivos[self.indice_actual]
        return None

    def obtener_lista_modelos(self):
        """Devuelve la lista de archivos .msh en la carpeta"""
        return list(self.archivos)

    def obtener_total_modelos(self):
        """Devuelve el total de modelos encontrados"""
        return self.total_modelos

    def obtener_carpeta(self):
        """Devuelve la carpeta actual"""
        return self.carpeta
