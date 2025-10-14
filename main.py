import sys
from PyQt6.QtWidgets import QApplication
from utils import Lector, filtrar_elementos_visibles, mapear_nodos
from main_window import MainWindow

def main():
    """Función principal de la aplicación"""
    # Cargar datos
    lector = Lector()
    lector.abrir_carpeta(r'./Para Visualizaciones/3D')
    print("Total de modelos:", lector.total_modelos)

    # Obtener modelo
    doc = lector.obtener_modelo(-1)
    coords, elements = doc["msh"]
    desplazamientos = doc["res"].get("desplazamientos")
    
    # Filtrar solo superficie visible
    coords, triangle_indices, line_indices, node_map = filtrar_elementos_visibles(coords, elements)
    
    # Mapear desplazamientos a nodos visibles
    desplazamientos = mapear_nodos(desplazamientos, node_map)

    # Crear aplicación
    app = QApplication(sys.argv)
    window = MainWindow(coords, triangle_indices, line_indices)
    window.show()
    
    window.set_data(coords,desplazamientos)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()