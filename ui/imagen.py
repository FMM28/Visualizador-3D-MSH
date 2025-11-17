"""Página de renderizado de imágenes"""
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QPushButton, 
                             QHBoxLayout, QFileDialog, QApplication, QSpinBox, 
                             QDialog, QMessageBox, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QStandardPaths
from datetime import datetime
from .styles import (get_page_style, FILE_BUTTON_STYLE, FOLDER_SELECT_BUTTON_STYLE, 
                     FILE_INFO_LABEL_STYLE)


class ImagePreviewDialog(QDialog):
    def __init__(self, pixmap, default_save_path, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.default_save_path = default_save_path
        self.setWindowTitle("Previsualización - Imagen Renderizada")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        info = QLabel(f"Resolución: {pixmap.width()} x {pixmap.height()} px | Formato: PNG")
        info.setStyleSheet("font-weight: bold; padding: 4px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        layout.addWidget(self.preview, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Guardar Imagen")
        save_btn.setStyleSheet(FOLDER_SELECT_BUTTON_STYLE)
        save_btn.clicked.connect(self._save_image)
        btn_layout.addWidget(save_btn)
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet(FILE_BUTTON_STYLE)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self._scale_image()

    def _scale_image(self):
        scaled = self.pixmap.scaled(self.width() - 50, self.height() - 150,
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
        self.preview.setPixmap(scaled)

    def resizeEvent(self, event):
        self._scale_image()
        super().resizeEvent(event)

    def _save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Imagen Renderizada", 
                                                    self.default_save_path, "Imágenes PNG (*.png)")
        if file_path:
            if not file_path.lower().endswith('.png'):
                file_path += '.png'
            if self.pixmap.save(file_path, 'PNG'):
                self.accept()


class ImagePage(QWidget):
    imageRendered = pyqtSignal(str)
    
    RATIO_CONFIG = {
        "Libre": {"ratio": None, "presets": [("1280x720", 1280, 720), ("1920x1080", 1920, 1080), ("2560x1440", 2560, 1440)]},
        "1:1 (Cuadrado)": {"ratio": (1, 1), "presets": [("512x512", 512, 512), ("1024x1024", 1024, 1024), ("2048x2048", 2048, 2048)]},
        "4:3 (Clásico)": {"ratio": (4, 3), "presets": [("1024x768", 1024, 768), ("1600x1200", 1600, 1200), ("2048x1536", 2048, 1536)]},
        "3:2 (Fotografía)": {"ratio": (3, 2), "presets": [("1500x1000", 1500, 1000), ("3000x2000", 3000, 2000)]},
        "16:9 (Widescreen)": {"ratio": (16, 9), "presets": [("1280x720", 1280, 720), ("1920x1080", 1920, 1080), ("2560x1440", 2560, 1440), ("3840x2160", 3840, 2160)]},
        "9:16 (Vertical)": {"ratio": (9, 16), "presets": [("720x1280", 720, 1280), ("1080x1920", 1080, 1920)]},
    }
    
    def __init__(self, gl_widget):
        super().__init__()
        self.gl_widget = gl_widget
        self.carpeta_modelos = None
        self._lock = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        config_group = QGroupBox("Configuración de Renderizado")
        config_layout = QVBoxLayout(config_group)
        
        # Ratio
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("Proporción:"))
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(self.RATIO_CONFIG.keys())
        self.ratio_combo.setCurrentText("16:9 (Widescreen)")
        self.ratio_combo.currentTextChanged.connect(self._on_ratio_changed)
        ratio_layout.addWidget(self.ratio_combo, 1)
        config_layout.addLayout(ratio_layout)
        
        # Resolución
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Ancho:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 8192)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(lambda: self._adjust_dimension('width'))
        res_layout.addWidget(self.width_spin)
        
        res_layout.addWidget(QLabel("Alto:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 8192)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")
        self.height_spin.valueChanged.connect(lambda: self._adjust_dimension('height'))
        res_layout.addWidget(self.height_spin)
        config_layout.addLayout(res_layout)
        
        # Presets
        self.presets_group = QGroupBox("Resoluciones comunes")
        self.presets_layout = QGridLayout(self.presets_group)
        config_layout.addWidget(self.presets_group)
        
        # Carpeta
        self.folder_label = QLabel()
        self.folder_label.setStyleSheet(FILE_INFO_LABEL_STYLE)
        self.folder_label.setWordWrap(True)
        config_layout.addWidget(self.folder_label)
        layout.addWidget(config_group)
        
        # Botón render
        render_btn = QPushButton("Renderizar Imagen")
        render_btn.setStyleSheet(FOLDER_SELECT_BUTTON_STYLE)
        render_btn.clicked.connect(self._render_image)
        render_btn.setMinimumHeight(40)
        layout.addWidget(render_btn)
        layout.addStretch()
        
        self.setStyleSheet(get_page_style())
        self._update_presets()
        self._update_folder_label()

    def _adjust_dimension(self, changed):
        if self._lock:
            return
        ratio = self.RATIO_CONFIG[self.ratio_combo.currentText()]["ratio"]
        if not ratio:
            return
        
        self._lock = True
        if changed == 'width':
            self.height_spin.setValue(round(self.width_spin.value() * ratio[1] / ratio[0]))
        else:
            self.width_spin.setValue(round(self.height_spin.value() * ratio[0] / ratio[1]))
        self._lock = False

    def _on_ratio_changed(self):
        self._update_presets()
        self._adjust_dimension('width')

    def _update_presets(self):
        while self.presets_layout.count():
            self.presets_layout.takeAt(0).widget().deleteLater()
        
        presets = self.RATIO_CONFIG[self.ratio_combo.currentText()]["presets"]
        for idx, (name, w, h) in enumerate(presets):
            btn = QPushButton(name)
            btn.setStyleSheet(FILE_BUTTON_STYLE)
            btn.setMinimumSize(100, 35)
            btn.clicked.connect(lambda _, w=w, h=h: self._set_resolution(w, h))
            self.presets_layout.addWidget(btn, idx // 2, idx % 2)

    def _set_resolution(self, width, height):
        self._lock = True
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self._lock = False

    def _get_save_directory(self):
        return (self.carpeta_modelos or 
                QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation) or 
                str(Path.home()))

    def _update_folder_label(self):
        self.folder_label.setText(f"Las imágenes se guardarán en: {self._get_save_directory()}")

    def set_carpeta_modelos(self, carpeta):
        self.carpeta_modelos = carpeta
        self._update_folder_label()

    def _render_image(self):
        try:
            original_size = self.gl_widget.size()
            self.gl_widget.makeCurrent()
            self.gl_widget.resize(self.width_spin.value(), self.height_spin.value())
            self.gl_widget.update()
            QApplication.processEvents()
            
            pixmap = self.gl_widget.grab()
            self.gl_widget.resize(original_size)
            self.gl_widget.update()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = str(Path(self._get_save_directory()) / f"render_{timestamp}.png")
            ImagePreviewDialog(pixmap, save_path, self).exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al renderizar: {str(e)}")

    def get_render_settings(self):
        return {
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'aspect_ratio': self.ratio_combo.currentText()
        }