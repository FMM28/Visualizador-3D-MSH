"""
Página de configuración de desplazamientos
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QSlider, QCheckBox, QFrame, QPushButton,
                             QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .styles import get_page_style, AXIS_BUTTON_STYLE, RANGE_LABEL_STYLE
import numpy as np

class DisplacementsPage(QWidget): 
    # Señales para comunicarse con la ventana principal
    displacements_toggled = pyqtSignal(int)
    factor_changed = pyqtSignal(int)
    gradient_axis_changed = pyqtSignal(str)
    
    AXIS_MAP = {'x': 0, 'y': 1, 'z': 2}
    
    SLIDER_RANGE = (0, 1000)
    SLIDER_DEFAULT = 100
    
    def __init__(self, gl_widget, displacement_data):
        super().__init__()
        self.gl_widget = gl_widget
        self.displacement_data = displacement_data
        self.current_axis = 'x'
        self.is_3d = np.any(self.displacement_data[:, 2] != 0.0)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet(get_page_style())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        layout.addWidget(self._create_title())
        layout.addWidget(self._create_displacement_group())
        layout.addWidget(self._create_gradient_group())
        layout.addStretch()
    
    def _create_title(self):
        """Crea el título de la página"""
        title = QLabel("Configuración de Desplazamientos")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0; padding: 8px 0; font-size: 13px;")
        return title
    
    def _create_separator(self):
        """Crea un separador visual horizontal"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #404040; max-height: 1px;")
        return separator
    
    def _create_displacement_group(self):
        """Crea el grupo de control de deformación"""
        group = QGroupBox("Control de Deformación")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Checkbox para activar/desactivar
        self.disp_checkbox = QCheckBox("Activar deformaciones")
        self.disp_checkbox.stateChanged.connect(self._on_toggle_displacements)
        layout.addWidget(self.disp_checkbox)
        layout.addWidget(self._create_separator())

        # Controles del factor de amplificación
        layout.addWidget(self._create_label("Factor de amplificación:"))
        
        self.factor_slider = QSlider(Qt.Orientation.Horizontal)
        self.factor_slider.setRange(*self.SLIDER_RANGE)
        self.factor_slider.setValue(self.SLIDER_DEFAULT)
        self.factor_slider.setEnabled(False)
        self.factor_slider.valueChanged.connect(self._on_factor_changed)
        layout.addWidget(self.factor_slider)

        self.factor_label = QLabel(f"Factor: {self.SLIDER_DEFAULT}")
        self.factor_label.setStyleSheet("font-size: 11px; color: #e0e0e0; font-weight: 600; padding: 4px;")
        layout.addWidget(self.factor_label)

        return group
    
    def _create_gradient_group(self):
        """Crea el grupo de control de gradientes"""
        group = QGroupBox("Visualización de Gradientes")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Checkbox principal
        self.gradient_checkbox = QCheckBox("Mostrar gradientes")
        self.gradient_checkbox.stateChanged.connect(self._on_toggle_gradient)
        layout.addWidget(self.gradient_checkbox)
        layout.addWidget(self._create_separator())

        # Controles de gradiente
        gradient_controls = QVBoxLayout()
        gradient_controls.setSpacing(8)
        
        gradient_controls.addWidget(self._create_label("Componente de desplazamiento:"))
        gradient_controls.addLayout(self._create_axis_buttons())
        
        # Info sobre rango de valores
        self.range_label = QLabel("Rango: --")
        self.range_label.setStyleSheet(RANGE_LABEL_STYLE)
        gradient_controls.addWidget(self.range_label)

        layout.addLayout(gradient_controls)
        
        # Inicialmente deshabilitar los botones de eje
        self._set_axis_buttons_enabled(False)

        return group
    
    def _create_label(self, text):
        """Crea un label con estilo predeterminado"""
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #b0b0b0; padding-top: 4px;")
        return label
    
    def _create_axis_buttons(self):
        """Crea los botones de selección de eje"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        
        self.axis_button_group = QButtonGroup(self)
        button_style = AXIS_BUTTON_STYLE
        
        buttons_config = [
            ('btn_x', "Eje X", 'x', 0, True),
            ('btn_y', "Eje Y", 'y', 1, True),
            ('btn_z', "Eje Z", 'z', 2, self.is_3d)
        ]
        
        for attr_name, text, axis, group_id, enabled in buttons_config:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(axis == 'x')
            btn.setMinimumHeight(32)
            btn.setStyleSheet(button_style)
            btn.setEnabled(bool(enabled))
            btn.clicked.connect(lambda checked, a=axis: self._on_axis_changed(a))
            
            if not enabled and axis == 'z':
                btn.setToolTip("Modelo 2D - Sin desplazamientos en Z")
            
            self.axis_button_group.addButton(btn, group_id)
            setattr(self, attr_name, btn)
            layout.addWidget(btn)
        
        return layout
    
    def _set_axis_buttons_enabled(self, enabled):
        """Habilita o deshabilita los botones de selección de eje"""
        self.btn_x.setEnabled(enabled)
        self.btn_y.setEnabled(enabled)
        self.btn_z.setEnabled(bool(enabled and self.is_3d))
    
    # Slots para eventos
    def _on_toggle_displacements(self, state):
        """Maneja el cambio de estado del checkbox de deformaciones"""
        is_checked = state == Qt.CheckState.Checked.value
        self.factor_slider.setEnabled(is_checked)
        self.displacements_toggled.emit(state)
    
    def _on_factor_changed(self, value):
        """Maneja el cambio del factor de amplificación"""
        self.factor_label.setText(f"Factor: {value}")
        self.factor_changed.emit(value)
    
    def _on_toggle_gradient(self, state):
        """Maneja el cambio de estado del checkbox de gradientes"""
        is_checked = state == Qt.CheckState.Checked.value
        self._set_axis_buttons_enabled(is_checked)
        
        if is_checked:
            if self.gl_widget:
                self.gl_widget.enable_gradient(True)
            self._update_gradient_values()
        else:
            if self.gl_widget:
                self.gl_widget.enable_gradient(False)
            self.range_label.setText("Rango: --")
    
    def _on_axis_changed(self, axis):
        """Maneja el cambio de eje seleccionado"""
        if axis == 'z' and not self.is_3d:
            return
            
        self.current_axis = axis
        
        if self.gradient_checkbox.isChecked():
            self._update_gradient_values()
        
        self.gradient_axis_changed.emit(axis)
    
    def _update_gradient_values(self):
        """Actualiza los valores de gradiente según el eje seleccionado"""
        if self.gl_widget is None:
            return
        
        col_index = self.AXIS_MAP.get(self.current_axis, 0)
        values = self.displacement_data[:, col_index].copy()
        
        self.gl_widget.set_node_values(values, auto_range=True)
        self.gl_widget.enable_gradient(True)
        
        val_min, val_max = np.min(values), np.max(values)
        self.range_label.setText(f"Rango: {val_min:.6f} a {val_max:.6f}")
    
    # Métodos públicos
    def is_checked(self):
        """Retorna si el checkbox está marcado"""
        return self.disp_checkbox.isChecked()
    
    def get_factor(self):
        """Retorna el valor actual del factor"""
        return self.factor_slider.value()
    
    def is_gradient_enabled(self):
        """Retorna si los gradientes están habilitados"""
        return self.gradient_checkbox.isChecked()
    
    def set_gradient_enabled(self, enabled):
        """Activa o desactiva los gradientes programáticamente"""
        self.gradient_checkbox.setChecked(enabled)
        self._set_axis_buttons_enabled(enabled)