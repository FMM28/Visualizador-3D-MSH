"""
Estilos centralizados para la aplicación
"""

# Estilo del panel lateral
SIDE_PANEL_STYLE = """
    QWidget {
        background-color: #2b2b2b;
        border-right: 1px solid #1a1a1a;
    }
"""

# Estilo de la barra de iconos
ICON_BAR_STYLE = """
    QWidget {
        background-color: #1e1e1e;
        border-right: 1px solid #0a0a0a;
    }
    QToolButton {
        background-color: transparent;
        border: none;
        padding: 10px;
        color: #ffffff;
        border-radius: 4px;
        margin: 2px;
    }
    QToolButton:hover {
        background-color: #3a3a3a;
    }
    QToolButton:checked {
        background-color: #2b2b2b;
        border-left: 3px solid #0d7dd6;
    }
"""

# Estilo del contenido de las páginas
PAGE_CONTENT_STYLE = """
    QWidget {
        background-color: transparent;
        color: #e0e0e0;
        border: none;
    }
    QGroupBox {
        color: #e0e0e0;
        font-weight: 600;
        font-size: 12px;
        border: 1px solid #404040;
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 12px;
        background-color: #333333;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #b0b0b0;
    }
    QLabel {
        background-color: transparent;
        border: none;
        padding: 3px;
        color: #b0b0b0;
        font-size: 11px;
    }
"""

# Estilo de ComboBox
COMBOBOX_STYLE = """
    QComboBox {
        background-color: #3a3a3a;
        border: 1px solid #505050;
        color: #e0e0e0;
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 11px;
        min-height: 20px;
    }
    QComboBox:hover {
        border: 1px solid #707070;
    }
    QComboBox::drop-down {
        border: none;
        width: 25px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
        color: #e0e0e0;
    }
    QComboBox QAbstractItemView {
        background-color: #3a3a3a;
        border: 1px solid #505050;
        border-radius: 4px;
        outline: none;
        color: #e0e0e0;
        selection-background-color: #0d7dd6;
        selection-color: #ffffff;
        font-size: 11px;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 12px;
        border-bottom: 1px solid #404040;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #0d7dd6;
        color: #ffffff;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #454545;
    }
"""

# Estilo de Slider
SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: #1a1a1a;
        height: 4px;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #0d7dd6;
        border: 1px solid #0a6bb5;
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }
    QSlider::handle:horizontal:hover {
        background: #1a8ae6;
    }
    QSlider::sub-page:horizontal {
        background: #0d7dd6;
        border-radius: 2px;
    }
"""

# Estilo de CheckBox
CHECKBOX_STYLE = """
    QCheckBox {
        background-color: transparent;
        color: #e0e0e0;
        padding: 6px;
        font-size: 11px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 1px solid #505050;
        background-color: #3a3a3a;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #707070;
    }
    QCheckBox::indicator:checked {
        background-color: #0d7dd6;
        border: 1px solid #0a6bb5;
    }
"""

# Estilo de botones
BUTTON_STYLE = """
    QPushButton {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #505050;
        padding: 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #454545;
        border: 1px solid #707070;
    }
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
"""

# Estilo del StackedWidget
STACKED_WIDGET_STYLE = """
    QStackedWidget {
        background-color: transparent;
        border: none;
    }
"""

# Combinar estilos comunes
def get_page_style():
    """Retorna el estilo completo para una página"""
    return PAGE_CONTENT_STYLE + COMBOBOX_STYLE + SLIDER_STYLE + CHECKBOX_STYLE