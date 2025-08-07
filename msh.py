import os
import threading

class LectorMsh:
    def __init__(self):
        self.carpeta = None
        self.archivos = []
        self.total_modelos = 0
        self.indice_actual = -1
        self.cache = {}
        self.lock = threading.Lock()
        self.thread_precarga = None
        self.detener_precarga = False

    def abrir_carpeta(self, carpeta):
        self.carpeta = carpeta
        self.archivos = sorted([
            f for f in os.listdir(carpeta) if f.lower().endswith('.msh')
        ])
        self.total_modelos = len(self.archivos)
        self.indice_actual = -1
        self.cache = {}

    def _leer_archivo(self, indice):
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
                        nodos = list(map(int, partes[1:-1]))
                        elementos.append(nodos)
                    i += 1
            else:
                i += 1

        return coordenadas, elementos

    def _cargar_modelo(self, indice):
        coords, elems = self._leer_archivo(indice)
        with self.lock:
            self.cache[indice] = (coords, elems)

    def _precargar_vecino(self, indice):
        if 0 <= indice < self.total_modelos:
            with self.lock:
                if indice in self.cache:
                    return
            if self.detener_precarga:
                return
            self._cargar_modelo(indice)

    def _iniciar_precarga(self, nuevo_indice):
        self.detener_precarga = True

        def precargar():
            self.detener_precarga = False
            vecinos = [nuevo_indice - 1, nuevo_indice + 1]
            for i in vecinos:
                if self.detener_precarga:
                    return
                self._precargar_vecino(i)

            with self.lock:
                claves_validas = {nuevo_indice - 1, nuevo_indice, nuevo_indice + 1}
                for k in list(self.cache.keys()):
                    if k not in claves_validas:
                        del self.cache[k]

        self.thread_precarga = threading.Thread(target=precargar, daemon=True)
        self.thread_precarga.start()

    def ir_a(self, indice):
        if not (0 <= indice < self.total_modelos):
            return False

        if indice not in self.cache:
            coords, elems = self._leer_archivo(indice)
            with self.lock:
                self.cache[indice] = (coords, elems)

        self.indice_actual = indice
        self._iniciar_precarga(indice)
        print(f"Cargado: {self.obtener_nombre_actual()}")
        return True


    def ir_al_primero(self):
        return self.ir_a(0)

    def ir_al_ultimo(self):
        return self.ir_a(self.total_modelos - 1)

    def ir_al_siguiente(self):
        return self.ir_a(self.indice_actual + 1)

    def ir_al_anterior(self):
        return self.ir_a(self.indice_actual - 1)

    def obtener_modelo_actual(self):
        with self.lock:
            return self.cache.get(self.indice_actual, (None, None))

    def obtener_nombre_actual(self):
        if 0 <= self.indice_actual < self.total_modelos:
            return self.archivos[self.indice_actual]
        return None
    
    def ver_cache(self):
        """Devuelve los índices actualmente en caché (ordenados)."""
        with self.lock:
            return sorted(self.cache.keys())
