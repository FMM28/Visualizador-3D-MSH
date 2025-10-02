"""
Modulo de seleccion de colores
"""
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                             QDialog, QSpinBox, QDialogButtonBox)
from PyQt6.QtGui import QColor

class ColorPickerDialog(QDialog):
    """Diálogo personalizado para selección de color RGB"""
    def __init__(self, initial_color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Color de Línea")
        self.setModal(True)
        self.selected_color = initial_color
        self._updating = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Preview del color
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(200, 60)
        self._update_preview()
        layout.addWidget(self.color_preview)
        
        # Controles RGB
        # Red
        r_layout = QHBoxLayout()
        r_label = QLabel("R:")
        r_label.setFixedWidth(30)
        self.r_spin = QSpinBox()
        self.r_spin.setRange(0, 255)
        self.r_spin.setValue(self.selected_color[0])
        self.r_spin.setStyleSheet("QSpinBox::up-button, QSpinBox::down-button { width: 0px; }")
        self.r_spin.valueChanged.connect(self._on_manual_color_changed)
        r_layout.addWidget(r_label)
        r_layout.addWidget(self.r_spin)
        layout.addLayout(r_layout)
        
        # Green
        g_layout = QHBoxLayout()
        g_label = QLabel("G:")
        g_label.setFixedWidth(30)
        self.g_spin = QSpinBox()
        self.g_spin.setRange(0, 255)
        self.g_spin.setValue(self.selected_color[1])
        self.g_spin.setStyleSheet("QSpinBox::up-button, QSpinBox::down-button { width: 0px; }")
        self.g_spin.valueChanged.connect(self._on_manual_color_changed)
        g_layout.addWidget(g_label)
        g_layout.addWidget(self.g_spin)
        layout.addLayout(g_layout)
        
        # Blue
        b_layout = QHBoxLayout()
        b_label = QLabel("B:")
        b_label.setFixedWidth(30)
        self.b_spin = QSpinBox()
        self.b_spin.setRange(0, 255)
        self.b_spin.setValue(self.selected_color[2])
        self.b_spin.setStyleSheet("QSpinBox::up-button, QSpinBox::down-button { width: 0px; }")
        self.b_spin.valueChanged.connect(self._on_manual_color_changed)
        b_layout.addWidget(b_label)
        b_layout.addWidget(self.b_spin)
        layout.addLayout(b_layout)
        
        # Alpha
        a_layout = QHBoxLayout()
        a_label = QLabel("A:")
        a_label.setFixedWidth(30)
        self.a_spin = QSpinBox()
        self.a_spin.setRange(0, 255)
        self.a_spin.setValue(self.selected_color[3])
        self.a_spin.setStyleSheet("QSpinBox::up-button, QSpinBox::down-button { width: 0px; }")
        self.a_spin.valueChanged.connect(self._on_manual_color_changed)
        a_layout.addWidget(a_label)
        a_layout.addWidget(self.a_spin)
        layout.addLayout(a_layout)
        
        # Separador
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #555;")
        layout.addWidget(separator)
        
        # Botón para abrir paleta de colores
        palette_btn = QPushButton("Abrir Paleta de Colores")
        palette_btn.clicked.connect(self._open_qt_color_dialog)
        layout.addWidget(palette_btn)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _on_manual_color_changed(self):
        """Actualiza el color cuando se cambian los spinboxes"""
        if self._updating:
            return
        
        self.selected_color = (
            self.r_spin.value(),
            self.g_spin.value(),
            self.b_spin.value(),
            self.a_spin.value()
        )
        self._update_preview()
    
    def _open_qt_color_dialog(self):
        """Abre la paleta de colores nativa de Qt"""
        from PyQt6.QtWidgets import QColorDialog
        
        # Convertir tupla RGBA a QColor
        r, g, b, a = self.selected_color
        current_color = QColor(r, g, b, a)
        
        # Abrir diálogo con soporte para alpha
        color = QColorDialog.getColor(
            current_color, 
            self, 
            "Seleccionar Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        
        if color.isValid():
            self._updating = True
            self.selected_color = (
                color.red(),
                color.green(),
                color.blue(),
                color.alpha()
            )
            # Actualizar spinboxes
            self.r_spin.setValue(color.red())
            self.g_spin.setValue(color.green())
            self.b_spin.setValue(color.blue())
            self.a_spin.setValue(color.alpha())
            self._update_preview()
            self._updating = False
    
    def _update_preview(self):
        """Actualiza la vista previa del color"""
        r, g, b, a = self.selected_color
        self.color_preview.setStyleSheet(
            f"background-color: rgba({r}, {g}, {b}, {a});"
            f"border: 2px solid #555; border-radius: 4px;"
        )
    
    def get_color(self):
        """Retorna el color seleccionado como tupla RGBA"""
        return self.selected_color
