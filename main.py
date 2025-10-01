import sys
from PyQt6.QtWidgets import QApplication
from utils import Lector, filtrar_elementos_visibles, mapear_desplazamientos
from main_window import MainWindow

def main():
    """Función principal de la aplicación"""
    # Cargar datos
    lector = Lector()
    lector.abrir_carpeta(r'./Para Visualizaciones/3D')
    print("Total de modelos:", lector.total_modelos)

    # Obtener modelo
    doc = lector.obtener_modelo(-1)
    coords_original, elements_original = doc["msh"]
    desplazamientos_original = doc["res"].get("desplazamientos")
    
    # Filtrar solo superficie visible
    coords, triangle_indices, line_indices, node_map = filtrar_elementos_visibles(coords_original, elements_original)
    
    # Mapear desplazamientos a nodos visibles
    desplazamientos = mapear_desplazamientos(desplazamientos_original, node_map)

    # Crear aplicación
    app = QApplication(sys.argv)
    window = MainWindow(coords, triangle_indices, line_indices, desplazamientos)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()