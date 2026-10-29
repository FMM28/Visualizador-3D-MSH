"""
Página de configuración de desplazamientos
"""
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from .gradient import GradientPage
from .styles import AXIS_BUTTON_STYLE, get_page_style


class DisplacementsPage(GradientPage):
    # Señales para comunicarse con la ventana principal
    displacements_toggled = pyqtSignal(int)
    factor_changed = pyqtSignal(int)
    gradient_axis_changed = pyqtSignal(str)

    AXIS_MAP = {'x': 0, 'y': 1, 'z': 2}

    SLIDER_RANGE = (0, 1000)
    SLIDER_DEFAULT = 100

    def __init__(self, gl_widget):
        super().__init__(gl_widget)
        self.displacement_data = None
        self.original_coords = None
        self.current_axis = 'x'
        self.is_3d = False
        self._data_loaded = False
        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet(get_page_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        layout.addWidget(self._create_title("Configuración de Desplazamientos"))
        layout.addWidget(self._create_displacement_group())
        layout.addWidget(self._create_gradient_group())
        layout.addStretch()

    def _create_displacement_group(self):
        """Crea el grupo de control de deformación"""
        group = QGroupBox("Control de Deformación")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Checkbox para activar/desactivar
        self.disp_checkbox = QCheckBox("Activar deformaciones")
        self.disp_checkbox.setEnabled(False)
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
        self.gradient_checkbox.setEnabled(False)
        self.gradient_checkbox.stateChanged.connect(self._on_toggle_gradient)
        layout.addWidget(self.gradient_checkbox)
        layout.addWidget(self._create_separator())

        # Controles de gradiente
        gradient_controls = QVBoxLayout()
        gradient_controls.setSpacing(8)

        gradient_controls.addWidget(self._create_label("Componente de desplazamiento:"))
        gradient_controls.addLayout(self._create_axis_buttons())

        # Info sobre rango de valores
        self.range_label = self._create_range_label()
        gradient_controls.addWidget(self.range_label)

        layout.addLayout(gradient_controls)

        # Inicialmente deshabilitar los botones de eje
        self._set_axis_buttons_enabled(False)

        return group

    def _create_axis_buttons(self):
        """Crea los botones de selección de eje"""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        self.axis_button_group = QButtonGroup(self)

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
            btn.setStyleSheet(AXIS_BUTTON_STYLE)
            btn.setEnabled(False)
            btn.clicked.connect(lambda checked, a=axis: self._on_axis_changed(a))

            if not enabled and axis == 'z':
                btn.setToolTip("Modelo 2D - Sin desplazamientos en Z")

            self.axis_button_group.addButton(btn, group_id)
            setattr(self, attr_name, btn)
            layout.addWidget(btn)

        return layout

    def _set_axis_buttons_enabled(self, enabled):
        """Habilita o deshabilita los botones de selección de eje"""
        if not self._data_loaded:
            enabled = False

        self.btn_x.setEnabled(enabled)
        self.btn_y.setEnabled(enabled)
        self.btn_z.setEnabled(bool(enabled and self.is_3d))

    # Slots para eventos
    def _on_toggle_displacements(self, state):
        """Maneja el cambio de estado del checkbox de deformaciones"""
        if not self._data_loaded:
            return

        is_checked = state == Qt.CheckState.Checked.value
        self.factor_slider.setEnabled(is_checked)

        if is_checked:
            self._update_displacements(self.factor_slider.value())
        else:
            self._reset_to_original()

        self.displacements_toggled.emit(state)

    def _on_factor_changed(self, value):
        """Maneja el cambio del factor de amplificación"""
        if not self._data_loaded:
            return

        self.factor_label.setText(f"Factor: {value}")

        if self.disp_checkbox.isChecked():
            self._update_displacements(value)

        self.factor_changed.emit(value)

    def _on_toggle_gradient(self, state):
        """Maneja el cambio de estado del checkbox de gradientes"""
        if not self._data_loaded:
            return

        is_checked = state == Qt.CheckState.Checked.value
        self._set_axis_buttons_enabled(is_checked)

        if is_checked:
            # Primero se avisa a las otras páginas para que suelten el gradiente
            self.gradient_activated.emit()
            self._update_gradient_values()
        else:
            self._disable_gl_gradient()

    def _on_gradient_released(self):
        """Otra página tomó el gradiente: deshabilitar los botones de eje"""
        self._set_axis_buttons_enabled(False)

    def _on_axis_changed(self, axis):
        """Maneja el cambio de eje seleccionado"""
        if not self._data_loaded or (axis == 'z' and not self.is_3d):
            return

        self.current_axis = axis

        if self.gradient_checkbox.isChecked():
            self._update_gradient_values()

        self.gradient_axis_changed.emit(axis)

    def _update_gradient_values(self):
        """Actualiza los valores de gradiente según el eje seleccionado"""
        if not self._data_loaded or self.gl_widget is None:
            return

        col_index = self.AXIS_MAP.get(self.current_axis, 0)
        self._apply_gradient_values(
            self.displacement_data[:, col_index],
            title=f"Desplazamiento {self.current_axis.upper()}",
        )

    def _update_displacements(self, factor):
        """Actualiza las coordenadas con desplazamientos amplificados"""
        if not self._data_loaded or self.displacement_data is None:
            return

        current_coords = self.original_coords + factor * self.displacement_data
        self.gl_widget.update_coords(current_coords)

    def _reset_to_original(self):
        """Restaura las coordenadas originales sin desplazamientos"""
        if not self._data_loaded or self.original_coords is None:
            return

        self.gl_widget.update_coords(self.original_coords.tolist())

    def _apply_current_state(self):
        """Aplica el estado actual de los checkboxes y controles al nuevo modelo"""
        if self.disp_checkbox.isChecked():
            self._update_displacements(self.factor_slider.value())

        if self.gradient_checkbox.isChecked():
            self._update_gradient_values()

    def _clear_data(self):
        """Deja la página sin datos (modelo sin desplazamientos)"""
        if self.is_gradient_active():
            self._disable_gl_gradient()

        self._data_loaded = False
        self.displacement_data = None
        self.original_coords = None

        for checkbox in (self.disp_checkbox, self.gradient_checkbox):
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.setEnabled(False)
            checkbox.blockSignals(False)

        self.factor_slider.setEnabled(False)
        self._set_axis_buttons_enabled(False)

    def set_data(self, original_coords, displacement_data):
        """Establece los datos necesarios para manejar desplazamientos"""
        if displacement_data is None:
            self._clear_data()
            return

        self.original_coords = original_coords.copy() if isinstance(original_coords, np.ndarray) else np.array(original_coords)
        self.displacement_data = displacement_data.copy() if isinstance(displacement_data, np.ndarray) else np.array(displacement_data)
        self.is_3d = bool(np.any(self.displacement_data[:, 2] != 0.0))
        self._data_loaded = True

        # Habilitar controles
        self.disp_checkbox.setEnabled(True)
        self.gradient_checkbox.setEnabled(True)

        # Actualizar estado del botón Z
        if not self.is_3d:
            self.btn_z.setEnabled(False)
            self.btn_z.setToolTip("Modelo 2D - Sin desplazamientos en Z")
            # Si el eje Z estaba seleccionado, cambiar a X
            if self.current_axis == 'z':
                self.current_axis = 'x'
                self.btn_x.setChecked(True)
        else:
            self.btn_z.setToolTip("")
            if self.gradient_checkbox.isChecked():
                self.btn_z.setEnabled(True)

        # Aplicar el estado guardado al nuevo modelo
        self._apply_current_state()