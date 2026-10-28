"""
Página de visualización de resultados (gradientes de campos nodales y por elemento)
"""
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QComboBox, QGroupBox, QVBoxLayout

from .gradient import GradientPage
from .styles import get_page_style


class ResultsPage(GradientPage):
    # Señales para comunicarse con la ventana principal
    field_changed = pyqtSignal(str)

    TIPOS_VALIDOS = {"point_data": "nodal", "cell_data": "elemento"}
    MAGNITUD = "Magnitud"

    def __init__(self, gl_widget):
        super().__init__(gl_widget)
        self.resultados = {}
        self.triangle_indices = np.empty((0, 3), dtype=np.int64)
        self.n_nodes = 0
        self._data_loaded = False
        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet(get_page_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        layout.addWidget(self._create_title("Visualización de Resultados"))
        layout.addWidget(self._create_results_group())
        layout.addStretch()

    def _create_results_group(self):
        """Crea el grupo de selección de campo y componente"""
        group = QGroupBox("Gradiente de Resultados")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Checkbox principal
        self.gradient_checkbox = QCheckBox("Mostrar gradiente")
        self.gradient_checkbox.setEnabled(False)
        self.gradient_checkbox.stateChanged.connect(self._on_toggle_gradient)
        layout.addWidget(self.gradient_checkbox)
        layout.addWidget(self._create_separator())

        # Selección de campo
        layout.addWidget(self._create_label("Campo:"))
        self.field_combo = QComboBox()
        self.field_combo.setEnabled(False)
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)
        layout.addWidget(self.field_combo)

        # Selección de componente
        layout.addWidget(self._create_label("Componente:"))
        self.component_combo = QComboBox()
        self.component_combo.setEnabled(False)
        self.component_combo.currentIndexChanged.connect(self._on_component_changed)
        layout.addWidget(self.component_combo)

        # Aviso para datos por elemento
        self.note_label = self._create_label("Valores por elemento promediados en los nodos")
        self.note_label.setWordWrap(True)
        self.note_label.hide()
        layout.addWidget(self.note_label)

        # Rango de valores
        self.range_label = self._create_range_label()
        layout.addWidget(self.range_label)

        return group

    def _on_toggle_gradient(self, state):
        """Maneja el cambio de estado del checkbox de gradiente"""
        if not self._data_loaded:
            return

        if state == Qt.CheckState.Checked.value:
            # Primero se avisa a las otras páginas para que suelten el gradiente
            self.gradient_activated.emit()
            self._update_gradient_values()
        else:
            self._disable_gl_gradient()

    def _on_field_changed(self, index):
        """Maneja el cambio de campo seleccionado"""
        if index < 0:
            return

        self._populate_components()
        self._update_note()

        if self.is_gradient_active():
            self._update_gradient_values()

        self.field_changed.emit(self.field_combo.currentText())

    def _on_component_changed(self, index):
        """Maneja el cambio de componente seleccionada"""
        if index >= 0 and self.is_gradient_active():
            self._update_gradient_values()

    def _is_valid(self, r):
        """Comprueba que un resultado se pueda representar como gradiente"""
        if not isinstance(r, dict) or r.get("tipo") not in self.TIPOS_VALIDOS:
            return False
        v = r.get("valores")
        return (isinstance(v, np.ndarray) and v.ndim in (1, 2) and len(v) > 0
                and np.issubdtype(v.dtype, np.number))

    def _field_label(self, r):
        return f"{r['nombre']} ({self.TIPOS_VALIDOS[r['tipo']]})"

    def _current_result(self):
        return self.resultados.get(self.field_combo.currentData())

    @classmethod
    def _component_names(cls, valores):
        """Nombres de componentes disponibles según la forma de los valores"""
        if valores.ndim == 1 or valores.shape[1] == 1:
            return ["Valor"]
        n = valores.shape[1]
        if n in (2, 3):
            return ["X", "Y", "Z"][:n] + [cls.MAGNITUD]
        return [f"Componente {i + 1}" for i in range(n)]

    def _populate_components(self, keep=None):
        """Rellena el combo de componentes para el campo actual"""
        r = self._current_result()
        self.component_combo.blockSignals(True)
        self.component_combo.clear()
        if r is not None:
            names = self._component_names(r["valores"])
            self.component_combo.addItems(names)
            if keep in names:
                self.component_combo.setCurrentText(keep)
        self.component_combo.setEnabled(self.component_combo.count() > 1)
        self.component_combo.blockSignals(False)

    def _update_note(self):
        r = self._current_result()
        self.note_label.setVisible(r is not None and r["tipo"] == "cell_data")

    def _extract_component(self, valores):
        """Devuelve un array 1D con la componente seleccionada"""
        if valores.ndim == 1:
            return valores
        if valores.shape[1] == 1:
            return valores[:, 0]
        if self.component_combo.currentText() == self.MAGNITUD:
            return np.linalg.norm(valores, axis=1)
        return valores[:, self.component_combo.currentIndex()]

    def _to_node_values(self, r, values):
        """
        Convierte los valores a un valor por nodo.
        point_data ya es nodal; cell_data (un valor por triángulo) se promedia
        en los nodos que comparten cada triángulo.
        """
        if r["tipo"] == "point_data":
            return values if len(values) == self.n_nodes else None

        tris = self.triangle_indices
        if len(values) != len(tris):
            return None

        flat = tris.ravel()
        sums = np.bincount(flat, weights=np.repeat(values, 3), minlength=self.n_nodes)
        counts = np.bincount(flat, minlength=self.n_nodes)
        counts[counts == 0] = 1
        return sums[:self.n_nodes] / counts[:self.n_nodes]

    def _update_gradient_values(self):
        """Calcula los valores nodales del campo/componente actual y los aplica"""
        if not self._data_loaded or self.gl_widget is None:
            return

        r = self._current_result()
        if r is None:
            return

        valores = np.asarray(r["valores"], dtype=np.float64)
        values = self._to_node_values(r, self._extract_component(valores))

        if values is None:
            self._disable_gl_gradient()
            self._clear_range("Rango: el tamaño del campo no coincide con la malla")
            return

        self._apply_gradient_values(values)

    def set_data(self, resultados, triangle_indices, n_nodes):
        """Establece los resultados del modelo cargado"""
        prev_field = self.field_combo.currentText()
        prev_component = self.component_combo.currentText()

        self.resultados = {k: r for k, r in (resultados or {}).items() if self._is_valid(r)}
        if triangle_indices is None:
            self.triangle_indices = np.empty((0, 3), dtype=np.int64)
        else:
            self.triangle_indices = np.asarray(triangle_indices, dtype=np.int64).reshape(-1, 3)
        self.n_nodes = int(n_nodes)
        self._data_loaded = bool(self.resultados)

        # Rellenar campos, conservando el seleccionado si existe en el nuevo modelo
        self.field_combo.blockSignals(True)
        self.field_combo.clear()
        for key, r in self.resultados.items():
            self.field_combo.addItem(self._field_label(r), key)
        idx = self.field_combo.findText(prev_field)
        self.field_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.field_combo.blockSignals(False)

        self._populate_components(keep=prev_component)
        self._update_note()

        self.field_combo.setEnabled(self._data_loaded)
        self.gradient_checkbox.setEnabled(self._data_loaded)

        if not self._data_loaded:
            if self.is_gradient_active():
                self._disable_gl_gradient()
                self._uncheck_gradient_silently()
            self.component_combo.setEnabled(False)
            return

        # Aplicar el estado guardado al nuevo modelo
        if self.is_gradient_active():
            self._update_gradient_values()