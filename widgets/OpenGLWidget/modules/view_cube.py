import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
    QTransform,
)
from PyQt6.QtWidgets import QVBoxLayout, QWidget

FACES = [
    ("front",  "FRONTAL",   (-1, 1, 1),  (1, 1, 1),   (-1, -1, 1)),
    ("back",   "TRASERA",   (1, 1, -1),  (-1, 1, -1), (1, -1, -1)),
    ("right",  "DERECHA",   (1, 1, 1),   (1, 1, -1),  (1, -1, 1)),
    ("left",   "IZQUIERDA", (-1, 1, -1), (-1, 1, 1),  (-1, -1, -1)),
    ("top",    "SUPERIOR",  (-1, 1, -1), (1, 1, -1),  (-1, 1, 1)),
    ("bottom", "INFERIOR",  (-1, -1, 1), (1, -1, 1),  (-1, -1, -1)),
]

BEVEL = 0.22
_BANDS = [(0.0, BEVEL), (BEVEL, 1 - BEVEL), (1 - BEVEL, 1.0)]

# Paleta
ACCENT = QColor(255, 154, 46)
BASE_RGB = np.array([92, 100, 116], float)
EDGE_PEN = QColor(18, 20, 24, 220)
AXES = [((1, 0, 0), "X", QColor(232, 86, 86)),
        ((0, 1, 0), "Y", QColor(120, 205, 95)),
        ((0, 0, 1), "Z", QColor(86, 150, 245))]


def _build_faces():
    """Precalcula cada cara dividida en 3x3 zonas: centro = cara, bordes = aristas,
    esquinas = vértices. Cada zona se identifica por el punto del cubo que representa."""
    faces = []
    for key, label, tl, tr, bl in FACES:
        tl, tr, bl = (np.array(v, float) for v in (tl, tr, bl))
        du, dv = tr - tl, bl - tl
        zones = []
        for i, (u0, u1) in enumerate(_BANDS):
            for j, (v0, v1) in enumerate(_BANDS):
                region = tuple(int(round(c)) for c in tl + du * (i / 2) + dv * (j / 2))
                quad = [tl + du * u + dv * v
                        for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
                zones.append((region, quad, i == 1 and j == 1))
        normal = tl + (du + dv) / 2
        faces.append((key, label, tl, du, dv, normal, zones))
    return faces


_FACES = _build_faces()
_FACE_BY_NORMAL = {tuple(int(c) for c in f[5]): f[0] for f in _FACES}


def _shade(rgb, k, alpha=245):
    r, g, b = np.clip(rgb * k, 0, 255).astype(int)
    return QColor(int(r), int(g), int(b), alpha)


class ViewCube(QWidget):
    SIZE, SCALE = 124, 26
    RING_RADIUS = 1.6           # anillo tipo brújula (en unidades del cubo)
    LABEL_BOX = 100.0           # caja local donde se maqueta el texto de cada cara

    def __init__(self, gl, parent=None):
        super().__init__(parent)
        self.gl = gl
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setMouseTracking(True)
        self._hits, self._hover = [], None
        self._fonts = {}

    # ---------- Proyección ----------

    def _projector(self):
        x_ax, y_ax, z_ax = self.gl.camera.view_axes()
        c, s = self.SIZE / 2, self.SCALE

        def proj(p):
            return QPointF(c + float(np.dot(p, x_ax)) * s, c - float(np.dot(p, y_ax)) * s)

        return proj, x_ax, y_ax, z_ax

    # ---------- Pintado ----------

    def paintEvent(self, _):
        if not self.gl.camera:
            return
        proj, x_ax, y_ax, z_ax = self._projector()

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        self._paint_backdrop(p)
        self._paint_ring(p, proj, z_ax, front=False)

        # Luz fija respecto a la vista (arriba-izquierda): da volumen al cubo
        light = -0.35 * x_ax + 0.6 * y_ax + 0.72 * z_ax
        light /= np.linalg.norm(light)

        self._hits = []
        for key, label, tl, du, dv, n, zones in _FACES:
            facing = float(np.dot(n, z_ax))
            if facing <= 0.01:                       # cara de espaldas
                continue
            k = 0.62 + 0.42 * max(float(np.dot(n, light)), 0.0)
            main, bevel = _shade(BASE_RGB, k), _shade(BASE_RGB, k * 0.74)

            # Bisel (toda la cara) y panel central más claro
            outer = QPolygonF([proj(tl), proj(tl + du), proj(tl + du + dv), proj(tl + dv)])
            p.setPen(QPen(EDGE_PEN, 1.0))
            p.setBrush(bevel)
            p.drawPolygon(outer)

            for region, quad, is_center in zones:
                poly = QPolygonF([proj(q) for q in quad])
                self._hits.append((region, poly))
                hovered = region == self._hover
                if not (is_center or hovered):
                    continue
                p.setPen(QPen(QColor(255, 255, 255, 30), 0.8) if is_center else Qt.PenStyle.NoPen)
                p.setBrush(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 235)
                           if hovered else main)
                p.drawPolygon(poly)

            self._paint_label(p, proj, tl, du, dv, label, facing,
                              dark=self._hover == tuple(int(c) for c in n))

        self._paint_ring(p, proj, z_ax, front=True)
        self._paint_axes(p, x_ax, y_ax, z_ax)
        p.end()

    def _paint_backdrop(self, p):
        c = self.SIZE / 2
        r = c - 2
        g = QRadialGradient(QPointF(c, c - r * 0.25), r * 1.1)
        g.setColorAt(0.0, QColor(64, 70, 84, 150))
        g.setColorAt(1.0, QColor(16, 18, 22, 110))
        p.setPen(QPen(QColor(255, 255, 255, 26), 1.0))
        p.setBrush(g)
        p.drawEllipse(QPointF(c, c), r, r)

    def _paint_ring(self, p, proj, z_ax, front):
        """Anillo a la altura de la base del cubo; se pinta en dos mitades
        (detrás y delante del cubo) para que se lea la profundidad."""
        t = np.linspace(0, 2 * np.pi, 73)
        pts = np.stack([np.cos(t), np.full_like(t, -1.0), np.sin(t)], axis=1)
        pts[:, [0, 2]] *= self.RING_RADIUS
        depth = pts @ z_ax
        # Trazos continuos (no segmentos sueltos) para que el anillo no salga punteado
        path, drawing = QPainterPath(), False
        for a, b, da, db in zip(pts[:-1], pts[1:], depth[:-1], depth[1:]):
            if ((da + db) >= 0) == front:
                if not drawing:
                    path.moveTo(proj(a))
                    drawing = True
                path.lineTo(proj(b))
            else:
                drawing = False
        p.setPen(QPen(QColor(255, 255, 255, 70 if front else 38), 1.6,
                      cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Marca del frente (+Z)
        if front == (float(np.dot([0, -1, self.RING_RADIUS], z_ax)) >= 0):
            tip = proj(np.array([0.0, -1.0, self.RING_RADIUS]))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 200))
            p.drawEllipse(tip, 2.6, 2.6)

    def _font_for(self, label):
        """Fuente en negrita que cabe en la caja local de la cara"""
        if label not in self._fonts:
            f = QFont()
            f.setBold(True)
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 104)
            size = 21
            f.setPixelSize(size)
            width = QFontMetricsF(f).horizontalAdvance(label)
            limit = self.LABEL_BOX * 0.74
            if width > limit:
                f.setPixelSize(max(9, int(size * limit / width)))
            self._fonts[label] = f
        return self._fonts[label]

    def _paint_label(self, p, proj, tl, du, dv, label, facing, dark):
        """Texto mapeado sobre la cara (sigue su perspectiva) y que se
        desvanece cuando la cara queda de canto."""
        alpha = np.clip((facing - 0.18) / 0.4, 0.0, 1.0)
        if alpha <= 0:
            return
        o, u, v = proj(tl), proj(tl + du), proj(tl + dv)
        L = self.LABEL_BOX
        t = QTransform((u.x() - o.x()) / L, (u.y() - o.y()) / L,
                       (v.x() - o.x()) / L, (v.y() - o.y()) / L,
                       o.x(), o.y())
        p.save()
        p.setTransform(t)
        p.setFont(self._font_for(label))
        p.setPen(QColor(25, 25, 25, int(255 * alpha)) if dark
                 else QColor(238, 240, 245, int(235 * alpha)))
        p.drawText(QRectF(0, 0, L, L), Qt.AlignmentFlag.AlignCenter, label)
        p.restore()

    def _paint_axes(self, p, x_ax, y_ax, z_ax):
        """Mini triedro XYZ en la esquina inferior izquierda"""
        ox, oy, length = 17.0, self.SIZE - 17.0, 11.0
        origin = QPointF(ox, oy)
        f = QFont()
        f.setBold(True)
        f.setPixelSize(8)
        p.setFont(f)
        # De atrás hacia delante para que el eje más cercano quede encima
        for axis, name, color in sorted(AXES, key=lambda a: float(np.dot(a[0], z_ax))):
            dx, dy = float(np.dot(axis, x_ax)), -float(np.dot(axis, y_ax))
            end = QPointF(ox + dx * length, oy + dy * length)
            p.setPen(QPen(color, 2.0, cap=Qt.PenCapStyle.RoundCap))
            p.drawLine(origin, end)
            if np.hypot(dx, dy) > 0.3:
                p.drawText(QRectF(ox + dx * (length + 5) - 5, oy + dy * (length + 5) - 5, 10, 10),
                           Qt.AlignmentFlag.AlignCenter, name)

    # ---------- Interacción ----------

    def _pick(self, pos):
        for region, poly in self._hits:
            if poly.containsPoint(pos, Qt.FillRule.OddEvenFill):
                return region
        return None

    def mouseMoveEvent(self, e):
        region = self._pick(e.position())
        if region != self._hover:
            self._hover = region
            self.setCursor(Qt.CursorShape.PointingHandCursor if region
                           else Qt.CursorShape.ArrowCursor)
            self.update()

    def mousePressEvent(self, e):
        region = self._pick(e.position())
        if region:
            face = _FACE_BY_NORMAL.get(region)
            if face:
                self.gl.go_to_view(face)            # cara: vista estándar
            else:
                self.gl.go_to_direction(region)     # arista o esquina
        self.gl.setFocus()   # para que los atajos sigan funcionando
        e.accept()           # no dejar pasar el clic al visor (evita rotar)

    def leaveEvent(self, _):
        self._hover = None
        self.unsetCursor()
        self.update()


class ViewControls(QWidget):
    """Contenedor del ViewCube en la esquina superior derecha del visor"""
    MARGIN = 12

    def __init__(self, gl):
        super().__init__(gl)
        self.gl = gl
        self.cube = ViewCube(gl, self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.cube)

        self.cube.setToolTip("Clic en una cara, arista o esquina para orientar la vista")
        self.adjustSize()
        gl.camera_changed.connect(self.cube.update)
        self.hide()

    def reposition(self):
        self.move(self.gl.width() - self.width() - self.MARGIN, self.MARGIN)
        self.raise_()