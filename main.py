import sys
from PyQt6.QtWidgets import QApplication
from utils import Lector, filtrar_elementos_visibles, mapear_nodos
from main_window import MainWindow

def main():
    """Función principal de la aplicación"""
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()