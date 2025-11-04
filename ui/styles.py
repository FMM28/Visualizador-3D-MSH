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

# Estilo de botones de eje
AXIS_BUTTON_STYLE = """
    QPushButton {
        background-color: #2a2a2a;
        border: 2px solid #404040;
        border-radius: 4px;
        color: #e0e0e0;
        font-weight: 600;
        padding: 6px 12px;
    }
    QPushButton:checked {
        background-color: #0d7377;
        border-color: #14FFEC;
        color: #ffffff;
    }
    QPushButton:hover:!checked {
        background-color: #353535;
        border-color: #505050;
    }
    QPushButton:disabled {
        background-color: #1a1a1a;
        color: #555555;
        border-color: #2a2a2a;
    }
"""

# Estilo de botones de paleta
PALETTE_BUTTON_STYLE = """
    QPushButton {
        background-color: #2d2d2d;
        border: 2px solid #404040;
        border-radius: 6px;
        padding: 6px;
        text-align: left;
    }
    QPushButton:hover {
        background-color: #353535;
        border-color: #4a90e2;
    }
    QPushButton:checked {
        background-color: #3a3a3a;
        border-color: #4a90e2;
        border-width: 3px;
    }
"""

# Estilo de label de rango
RANGE_LABEL_STYLE = """
    font-size: 10px; 
    color: #888888; 
    padding: 8px;
    background-color: #1a1a1a;
    border-radius: 3px;
    margin-top: 8px;
"""

# Estilo del StackedWidget
STACKED_WIDGET_STYLE = """
    QStackedWidget {
        background-color: transparent;
        border: none;
    }
"""

# Estilo de ScrollArea
SCROLL_AREA_STYLE = """
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        background-color: #2d2d2d;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background-color: #4a4a4a;
        border-radius: 6px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #5a5a5a;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
"""

# Estilo para etiquetas de nombre de paleta
PALETTE_NAME_LABEL_STYLE = """
    font-size: 11px; 
    font-weight: 600; 
    color: #e0e0e0;
    background-color: transparent;
    border: none;
    padding: 0px;
"""

# Estilos para la página de archivos
FILE_BUTTON_STYLE = """
    QPushButton {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 1px solid #404040;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 11px;
        text-align: left;
    }
    QPushButton:hover {
        background-color: #353535;
        border-color: #505050;
    }
    QPushButton:checked {
        background-color: #0d7dd6;
        border-color: #0d7dd6;
        color: #ffffff;
    }
"""

FOLDER_SELECT_BUTTON_STYLE = """
    QPushButton {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #505050;
        padding: 10px 16px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #454545;
        border-color: #606060;
    }
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
"""

FILE_INFO_LABEL_STYLE = """
    QLabel {
        font-size: 11px;
        color: #b0b0b0;
        padding: 8px;
        background-color: #252525;
        border-radius: 3px;
        border: none;
    }
"""

FILE_SCROLL_AREA_STYLE = """
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        background-color: transparent;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #4a4a4a;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #5a5a5a;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        background-color: transparent;
        height: 8px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background-color: #4a4a4a;
        border-radius: 4px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #5a5a5a;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: transparent;
    }
"""

PROGRESS_DIALOG_STYLE = """
    QProgressDialog {
        font-size: 13px;
    }
    QProgressDialog QLabel {
        font-size: 13px;
        padding: 10px;
        min-height: 40px;
    }
    QProgressBar {
        border: 2px solid #3498db;
        border-radius: 5px;
        text-align: center;
        font-size: 12px;
        font-weight: bold;
    }
    QProgressBar::chunk {
        background-color: #3498db;
        border-radius: 3px;
    }
"""

# Estilo completo para la página de paletas
PALETTE_PAGE_STYLE = PAGE_CONTENT_STYLE + SCROLL_AREA_STYLE

# Mantener compatibilidad con código existente
def get_page_style():
    """Retorna el estilo completo para una página"""
    return PAGE_CONTENT_STYLE + COMBOBOX_STYLE + SLIDER_STYLE + CHECKBOX_STYLE