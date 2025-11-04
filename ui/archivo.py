"""
Página de selección de archivos con barra de progreso
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                             QLabel, QPushButton,
                             QButtonGroup, QFileDialog, QScrollArea,
                             QProgressDialog, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import (get_page_style, FILE_BUTTON_STYLE, FOLDER_SELECT_BUTTON_STYLE, 
                     FILE_INFO_LABEL_STYLE, FILE_SCROLL_AREA_STYLE, PROGRESS_DIALOG_STYLE)
from utils import Lector, filtrar_elementos_visibles, mapear_nodos

class ArchivePage(QWidget):
    archivo_seleccionado = pyqtSignal(str)
    modelo_cargado = pyqtSignal(dict)
    carpeta_cambiada = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.lector = Lector()
        self.botones_archivos = QButtonGroup()
        self.botones_archivos.setExclusive(True)
        self.carpeta_actual = None
        self.archivo_actual = None
        self.progress_dialog = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(12)
        
        # Grupo para la selección de carpeta
        grupo_carpeta = QGroupBox("Selección de Carpeta")
        layout_carpeta = QVBoxLayout(grupo_carpeta)
        layout_carpeta.setSpacing(8)
        
        # Botón para seleccionar carpeta
        self.btn_seleccionar_carpeta = QPushButton("Seleccionar Carpeta")
        self.btn_seleccionar_carpeta.setStyleSheet(FOLDER_SELECT_BUTTON_STYLE)
        self.btn_seleccionar_carpeta.clicked.connect(self._abrir_selector_carpeta)
        layout_carpeta.addWidget(self.btn_seleccionar_carpeta)
        
        # Label para mostrar la ruta seleccionada
        self.label_ruta = QLabel("No se ha seleccionado ninguna carpeta")
        self.label_ruta.setStyleSheet(FILE_INFO_LABEL_STYLE)
        self.label_ruta.setWordWrap(True)
        layout_carpeta.addWidget(self.label_ruta)
        
        layout_principal.addWidget(grupo_carpeta)
        
        # Grupo para la lista de archivos (inicialmente oculto)
        self.grupo_archivos = QGroupBox("Archivos Disponibles")
        layout_archivos = QVBoxLayout(self.grupo_archivos)
        layout_archivos.setSpacing(8)
        layout_archivos.setContentsMargins(8, 12, 8, 8)
        
        # Área de scroll para la lista de archivos
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(FILE_SCROLL_AREA_STYLE)
        
        # Widget contenedor para los botones de archivos
        self.contenedor_archivos = QWidget()
        self.layout_archivos = QVBoxLayout(self.contenedor_archivos)
        self.layout_archivos.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_archivos.setSpacing(4)
        self.layout_archivos.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.contenedor_archivos)
        layout_archivos.addWidget(self.scroll_area)
        
        # Label para cuando no hay archivos
        self.label_sin_archivos = QLabel("No hay archivos validos en la carpeta seleccionada")
        self.label_sin_archivos.setStyleSheet(FILE_INFO_LABEL_STYLE)
        self.label_sin_archivos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_archivos.addWidget(self.label_sin_archivos)
        self.label_sin_archivos.hide()
        
        layout_principal.addWidget(self.grupo_archivos)

        self.grupo_archivos.hide()
        
        self.setStyleSheet(get_page_style())
    
    def _mostrar_progreso(self, titulo, mensaje, max_value=0):
        """Crea y muestra un diálogo de progreso modal"""
        self.progress_dialog = QProgressDialog(mensaje, None, 0, max_value, self)
        self.progress_dialog.setWindowTitle(titulo)
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setCancelButton(None)
        
        # Ajustar tamaño y estilo
        self.progress_dialog.setMinimumWidth(400)
        self.progress_dialog.setMinimumHeight(120)
        self.progress_dialog.setStyleSheet(PROGRESS_DIALOG_STYLE)
        
        self.progress_dialog.show()
        QApplication.processEvents()
    
    def _actualizar_progreso(self, valor, mensaje=None):
        """Actualiza el valor y opcionalmente el mensaje del progreso"""
        if self.progress_dialog:
            self.progress_dialog.setValue(valor)
            if mensaje:
                self.progress_dialog.setLabelText(mensaje)
            QApplication.processEvents()
    
    def _cerrar_progreso(self):
        """Cierra el diálogo de progreso"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
    
    def _abrir_selector_carpeta(self):
        """Abre el diálogo para seleccionar carpeta"""
        ruta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta","",QFileDialog.Option.ShowDirsOnly)
        
        if ruta:
            self._cargar_archivos_desde_carpeta(ruta)
    
    def _cargar_archivos_desde_carpeta(self, ruta):
        """Carga los archivos desde la carpeta seleccionada"""
        # Mostrar barra de progreso
        self._mostrar_progreso("Cargando", "Escaneando carpeta...")
        
        try:
            # Detectar si cambió de carpeta
            carpeta_cambio = (self.carpeta_actual != ruta)
            self.carpeta_actual = ruta
            
            # Si cambió de carpeta, resetear archivo actual
            if carpeta_cambio:
                self.archivo_actual = None
            
            self.lector.abrir_carpeta(ruta)
            self.label_ruta.setText(f"Carpeta seleccionada: {ruta}")
            
            self._limpiar_botones_archivos()
            
            # Obtener la lista de archivos
            archivos = self.lector.archivos_msh
            
            if archivos:
                self.label_sin_archivos.hide()
                self._crear_botones_archivos(archivos)
                self.grupo_archivos.show()
                
                # Emitir señal solo si cambió de carpeta
                if carpeta_cambio:
                    self.carpeta_cambiada.emit()
            else:
                self.label_sin_archivos.setText("No se encontraron archivos validos en la carpeta seleccionada")
                self.label_sin_archivos.show()
                self.grupo_archivos.show()
                
        except Exception as e:
            self.label_ruta.setText(f"Error al cargar la carpeta: {str(e)}")
            self._limpiar_botones_archivos()
            self.label_sin_archivos.setText(f"Error: {str(e)}")
            self.label_sin_archivos.show()
            self.grupo_archivos.show()
        finally:
            self._cerrar_progreso()
    
    def _limpiar_botones_archivos(self):
        """Limpia todos los botones de archivos existentes, preservando label_sin_archivos"""
        for i in reversed(range(self.layout_archivos.count())):
            widget = self.layout_archivos.itemAt(i).widget()
            if widget and widget != self.label_sin_archivos:
                widget.deleteLater()
        
        self.botones_archivos = QButtonGroup()
        self.botones_archivos.setExclusive(True)
    
    def _crear_botones_archivos(self, archivos):
        """Crea botones para cada archivo en la lista"""
        for idx, archivo in enumerate(archivos):
            btn_archivo = QPushButton(archivo)
            btn_archivo.setStyleSheet(FILE_BUTTON_STYLE)
            btn_archivo.setCheckable(True)
            btn_archivo.clicked.connect(lambda checked, i=idx, a=archivo: self._on_archivo_seleccionado(i, a))
            
            self.layout_archivos.insertWidget(self.layout_archivos.count() - 1, btn_archivo)
            self.botones_archivos.addButton(btn_archivo)
    
    def _on_archivo_seleccionado(self, idx, archivo):
        """Maneja la selección de un archivo"""

        if self.archivo_actual == archivo:
            return
        
        self._mostrar_progreso("Cargando Modelo", f"Cargando {archivo}...", 100)
        
        try:
            self._actualizar_progreso(20, f"Cargando {archivo}...")
            self.archivo_seleccionado.emit(archivo)
            
            # Obtener modelo
            self._actualizar_progreso(40, "Leyendo datos del archivo...")
            doc = self.lector.obtener_modelo(idx)
            coords, elements = doc["msh"]
            desplazamientos = doc["res"].get("desplazamientos")
            
            # Filtrar elementos visibles
            self._actualizar_progreso(60, "Procesando geometría...")
            coords, triangle_indices, line_indices, node_map = filtrar_elementos_visibles(coords, elements)
            
            self._actualizar_progreso(80, "Procesando desplazamientos...")
            desplazamientos = mapear_nodos(desplazamientos, node_map)
            
            # Emitir señal con los datos procesados
            self._actualizar_progreso(95, "Finalizando...")
            datos_modelo = {
                'coords': coords,
                'triangle_indices': triangle_indices,
                'line_indices': line_indices,
                'desplazamientos': desplazamientos
            }
            self.modelo_cargado.emit(datos_modelo)
            
            self._actualizar_progreso(100, "¡Completado!")
            
            # Guardar archivo actual después de carga exitosa
            self.archivo_actual = archivo
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Error al cargar el modelo: {str(e)}")
        finally:
            self._cerrar_progreso()