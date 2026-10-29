"""
Barra de colores (leyenda) superpuesta al área de renderizado
"""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class ColorBar(QWidget):
    """Leyenda vertical con la paleta activa y el rango de valores del gradiente"""

    NUM_TICKS = 6
    BAR_WIDTH = 18
    TICK_LENGTH = 4
    LABEL_GAP = 4
    MARGIN = 16            # Separación con el borde del área de render
    PADDING = 10           # Relleno interno del recuadro
    MAX_TITLE_WIDTH = 220
    BAR_HEIGHT_RANGE = (120, 320)
    BAR_HEIGHT_RATIO = 0.4  # Fracción de la altura del área de render

    # Posiciones disponibles: clave -> (alineación horizontal, alineación vertical)
    POSITIONS = {
        "right":        ("right", "center"),
        "left":         ("left", "center"),
        "top_right":    ("right", "top"),
        "bottom_right": ("right", "bottom"),
        "top_left":     ("left", "top"),
        "bottom_left":  ("left", "bottom"),
    }
    DEFAULT_POSITION = "right"

    BG_COLOR = QColor(25, 25, 25, 210)
    BORDER_COLOR = QColor(64, 64, 64)
    TEXT_COLOR = QColor(224, 224, 224)

    def __init__(self, parent):
        super().__init__(parent)
        # No bloquear rotación / pan / zoom del área de render
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._colors = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]
        self._vmin = 0.0
        self._vmax = 1.0
        self._title = ""
        self._ticks = []
        self._bar_height = self.BAR_HEIGHT_RANGE[0]
        self._position = self.DEFAULT_POSITION

        self._font = QFont()
        self._font.setPointSize(9)
        self._title_font = QFont(self._font)
        self._title_font.setBold(True)

        self.hide()

    def set_colors(self, colors):
        """Establece los colores de la paleta (lista de tuplas RGB 0-1)"""
        if colors:
            self._colors = [tuple(float(c) for c in color) for color in colors]
        self.update()

    def set_range(self, vmin, vmax):
        """Establece el rango de valores mostrado"""
        self._vmin, self._vmax = float(vmin), float(vmax)
        self.reposition()

    def set_title(self, title):
        """Establece el título de la barra (campo / componente)"""
        self._title = title or ""
        self.reposition()

    def set_position(self, position):
        """Coloca la barra en una de las posiciones de POSITIONS"""
        if position not in self.POSITIONS:
            return False
        self._position = position
        self.reposition()
        return True

    def position(self):
        """Posición actual (clave de POSITIONS)"""
        return self._position

    def reposition(self):
        """Recalcula tamaño y posición respecto al área de render"""
        parent = self.parentWidget()
        if parent is None:
            return

        self._ticks = self._compute_ticks()
        fm = self._metrics(self._font)
        tfm = self._metrics(self._title_font)

        # +2 px de holgura para evitar recortes por redondeo
        label_w = max((fm.horizontalAdvance(text) for _, text in self._ticks), default=0) + 2
        content_w = self.BAR_WIDTH + self.TICK_LENGTH + self.LABEL_GAP + label_w
        title_w = min(tfm.horizontalAdvance(self._title) + 2, self.MAX_TITLE_WIDTH) if self._title else 0
        width = 2 * self.PADDING + max(content_w, title_w)

        lo, hi = self.BAR_HEIGHT_RANGE
        self._bar_height = int(min(max(parent.height() * self.BAR_HEIGHT_RATIO, lo), hi))
        height = 2 * self.PADDING + self._title_height() + self._bar_height + fm.height()

        self.setFixedSize(width, height)

        h_align, v_align = self.POSITIONS[self._position]
        if h_align == "left":
            x = self.MARGIN
        else:
            x = parent.width() - width - self.MARGIN

        if v_align == "top":
            y = self.MARGIN
        elif v_align == "bottom":
            y = parent.height() - height - self.MARGIN
        else:
            y = (parent.height() - height) // 2

        self.move(max(x, 0), max(y, 0))
        self.update()

    def _metrics(self, font):
        """Métricas medidas contra este widget (mismo DPI que al pintar)"""
        return QFontMetrics(font, self)

    def _title_height(self):
        return self._metrics(self._title_font).height() + 6 if self._title else 0

    def _compute_ticks(self):
        """Devuelve [(fracción 0-1 desde abajo, texto), ...]"""
        span = self._vmax - self._vmin
        if span <= 0:
            return [(0.0, self._format(self._vmin, abs(self._vmin)))]

        scale = max(abs(self._vmin), abs(self._vmax))
        ticks = []
        for i in range(self.NUM_TICKS):
            frac = i / (self.NUM_TICKS - 1)
            value = self._vmin + frac * span
            if abs(value) < span * 1e-9:   # Evitar "-1.2e-17" en lugar de 0
                value = 0.0
            ticks.append((frac, self._format(value, scale)))
        return ticks

    @staticmethod
    def _format(value, scale):
        """Formato uniforme para todas las etiquetas según la magnitud del rango"""
        if scale != 0 and (scale >= 1e4 or scale < 1e-2):
            return f"{value:.3e}"
        return f"{value:.4g}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = self._metrics(self._font)
        tfm = self._metrics(self._title_font)

        # Fondo
        painter.setPen(QPen(self.BORDER_COLOR, 1))
        painter.setBrush(self.BG_COLOR)
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)

        y = self.PADDING
        inner_w = self.width() - 2 * self.PADDING

        # Título
        if self._title:
            painter.setFont(self._title_font)
            painter.setPen(self.TEXT_COLOR)
            text = tfm.elidedText(self._title, Qt.TextElideMode.ElideRight, inner_w)
            painter.drawText(QRectF(self.PADDING, y, inner_w, tfm.height()),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
            y += self._title_height()

        # Espacio para que la etiqueta superior no se salga del recuadro
        y += fm.height() / 2
        bar = QRectF(self.PADDING, y, self.BAR_WIDTH, self._bar_height)

        # Gradiente: mínimo abajo, máximo arriba (interpolación lineal como la textura 1D)
        gradient = QLinearGradient(bar.bottomLeft(), bar.topLeft())
        n = len(self._colors)
        for i, color in enumerate(self._colors):
            gradient.setColorAt(i / (n - 1) if n > 1 else 0.0, QColor.fromRgbF(*color))
        if n == 1:
            gradient.setColorAt(1.0, QColor.fromRgbF(*self._colors[0]))

        painter.setBrush(gradient)
        painter.setPen(QPen(self.BORDER_COLOR, 1))
        painter.drawRect(bar)

        # Marcas y etiquetas
        painter.setFont(self._font)
        painter.setPen(QPen(self.TEXT_COLOR, 1))
        x_tick = bar.right()
        x_text = x_tick + self.TICK_LENGTH + self.LABEL_GAP
        for frac, label in self._ticks:
            ty = bar.bottom() - frac * bar.height()
            painter.drawLine(QPointF(x_tick, ty), QPointF(x_tick + self.TICK_LENGTH, ty))
            painter.drawText(QRectF(x_text, ty - fm.height() / 2, self.width() - x_text, fm.height()),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

        painter.end()