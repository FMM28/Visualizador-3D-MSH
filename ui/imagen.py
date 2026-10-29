"""Página de renderizado de imágenes"""
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QEvent, QStandardPaths, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .image_viewer import FullScreenImageViewer
from .styles import (
    DIALOG_BUTTON_SIZE,
    DIALOG_BUTTON_STYLE,
    FIELD_HEIGHT,
    FILE_BUTTON_STYLE,
    FILE_INFO_LABEL_STYLE,
    FOLDER_SELECT_BUTTON_STYLE,
    SPIN_HIDDEN_ARROWS_STYLE,
    STEP_BUTTON_STYLE,
    get_page_style,
)


class ImagePreviewDialog(QDialog):
    def __init__(self, pixmap, default_save_path, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.default_save_path = default_save_path
        self._viewer = None
        self.setWindowTitle("Previsualización - Imagen Renderizada")
        self.setModal(True)
        self.setMinimumSize(800, 600)
 
        layout = QVBoxLayout(self)
        info = QLabel(f"Resolución: {pixmap.width()} x {pixmap.height()} px | Formato: PNG")
        info.setStyleSheet("font-weight: bold; padding: 4px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
 
        # La previsualización se adapta al espacio disponible (sin forzar el tamaño del diálogo)
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.preview.setMinimumSize(200, 150)
        self.preview.setToolTip("Doble clic para ver en pantalla completa")
        self.preview.installEventFilter(self)
        layout.addWidget(self.preview, 1)
 
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self._create_button(
            "Pantalla Completa", self._open_fullscreen,
            "Ver la imagen a pantalla completa con zoom (F11)"))
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_button("Guardar Imagen", self._save_image))
        btn_layout.addWidget(self._create_button("Cerrar", self.reject))
        layout.addLayout(btn_layout)
 
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, activated=self._open_fullscreen)
 
    def _create_button(self, text, slot, tooltip=None):
        """Crea un botón del diálogo con estilo y tamaño uniformes"""
        btn = QPushButton(text)
        btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        btn.setFixedSize(*DIALOG_BUTTON_SIZE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        return btn
 
    def eventFilter(self, obj, event):
        if obj is self.preview:
            if event.type() == QEvent.Type.Resize:
                self._scale_image()
            elif (event.type() == QEvent.Type.MouseButtonDblClick
                  and event.button() == Qt.MouseButton.LeftButton):
                self._open_fullscreen()
                return True
        return super().eventFilter(obj, event)
 
    def _scale_image(self):
        """Escala la imagen al tamaño de la previsualización usando los píxeles físicos de la pantalla"""
        if self.preview.width() <= 2 or self.preview.height() <= 2:
            return
        dpr = self.devicePixelRatioF()
        target = self.preview.contentsRect().size() * dpr
        scaled = self.pixmap.scaled(target,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        scaled.setDevicePixelRatio(dpr)
        self.preview.setPixmap(scaled)
 
    def _open_fullscreen(self):
        """Abre la imagen en un visor a pantalla completa"""
        self._viewer = FullScreenImageViewer(self.pixmap, self)
        self._viewer.showFullScreen()
 
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
 
    STEP_SIZE = 10   # Píxeles por clic en los botones − / +
 
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
 
        # Proporción, ancho y alto en una rejilla: cada uno en su propia fila,
        # con las etiquetas alineadas en la primera columna
        fields_layout = QGridLayout()
        fields_layout.setHorizontalSpacing(6)
        fields_layout.setVerticalSpacing(8)
        fields_layout.setColumnStretch(2, 1)
 
        # Proporción
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(self.RATIO_CONFIG.keys())
        self.ratio_combo.setCurrentText("16:9 (Widescreen)")
        self.ratio_combo.setMinimumHeight(FIELD_HEIGHT)
        self.ratio_combo.currentTextChanged.connect(self._on_ratio_changed)
        fields_layout.addWidget(QLabel("Proporción:"), 0, 0)
        fields_layout.addWidget(self.ratio_combo, 0, 1, 1, 3)
 
        # Ancho y alto
        self.width_spin = self._create_dimension_spin(1920, 'width')
        self.height_spin = self._create_dimension_spin(1080, 'height')
        self._add_dimension_row(fields_layout, 1, "Ancho:", self.width_spin)
        self._add_dimension_row(fields_layout, 2, "Alto:", self.height_spin)
 
        config_layout.addLayout(fields_layout)
 
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
 
    def _create_dimension_spin(self, value, dimension):
        """
        Campo numérico de resolución sin las flechas nativas: los botones − / +
        van fuera del campo, así el valor nunca queda tapado.
        """
        spin = QSpinBox()
        spin.setRange(100, 8192)
        spin.setValue(value)
        spin.setSuffix(" px")
        spin.setStyleSheet(SPIN_HIDDEN_ARROWS_STYLE)
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin.setFixedHeight(FIELD_HEIGHT)
        spin.setMinimumWidth(80)
        spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        spin.valueChanged.connect(lambda: self._adjust_dimension(dimension))
        return spin
 
    def _create_step_button(self, text, spin, step, tooltip):
        """Botón − / + que ajusta un campo de resolución (se repite al mantenerlo pulsado)"""
        btn = QPushButton(text)
        btn.setStyleSheet(STEP_BUTTON_STYLE)
        btn.setFixedSize(FIELD_HEIGHT, FIELD_HEIGHT)
        btn.setAutoRepeat(True)
        btn.setAutoRepeatDelay(400)
        btn.setAutoRepeatInterval(60)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setToolTip(tooltip)
        btn.clicked.connect(lambda: spin.stepBy(step))
        return btn
 
    def _add_dimension_row(self, grid, row, label, spin):
        """Añade una fila: etiqueta | − | campo | +"""
        grid.addWidget(QLabel(label), row, 0)
        grid.addWidget(self._create_step_button(
            "−", spin, -self.STEP_SIZE, f"Reducir {self.STEP_SIZE} px"), row, 1)
        grid.addWidget(spin, row, 2)
        grid.addWidget(self._create_step_button(
            "+", spin, self.STEP_SIZE, f"Aumentar {self.STEP_SIZE} px"), row, 3)
 
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
        """Renderiza la escena fuera de pantalla a la resolución exacta elegida"""
        width, height = self.width_spin.value(), self.height_spin.value()
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            image = self.gl_widget.render_to_image(width, height)
        except (RuntimeError, ValueError) as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "No se pudo renderizar", str(e))
            return
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"Error al renderizar: {str(e)}")
            return
        QApplication.restoreOverrideCursor()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = str(Path(self._get_save_directory()) / f"render_{timestamp}.png")
        ImagePreviewDialog(QPixmap.fromImage(image), save_path, self).exec()
 
    def get_render_settings(self):
        return {
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'aspect_ratio': self.ratio_combo.currentText()
        }