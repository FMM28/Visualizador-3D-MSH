import numpy as np

from utils import Matrix44

PITCH_LIMIT = np.pi / 2 - 0.01

VIEWS = {
    "front":  (np.pi / 2,  0.0),
    "back":   (-np.pi / 2, 0.0),
    "right":  (0.0,        0.0),
    "left":   (np.pi,      0.0),
    "top":    (np.pi / 2,  PITCH_LIMIT),
    "bottom": (np.pi / 2, -PITCH_LIMIT),
    "iso":    (np.pi / 4,  np.radians(35.264)),
}

DEFAULT_VIEW = "front"


class Camera:
    def __init__(self, center, radius):
        self.center = np.array(center, dtype=float)
        self._home_center = self.center.copy()
        self.radius = radius
        self.reset()

    def reset(self):
        self.center = self._home_center.copy()
        self.distance = self.radius * 2.5
        self.rotation_y, self.rotation_x = VIEWS[DEFAULT_VIEW]
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom_speed = 0.1
        self.rotation_speed = 0.01
        self.pan_speed = 0.001

    def _direction(self):
        return np.array([
            np.cos(self.rotation_y) * np.cos(self.rotation_x),
            np.sin(self.rotation_x),
            np.sin(self.rotation_y) * np.cos(self.rotation_x),
        ], dtype=float)

    def get_view_matrix(self):
        target = np.array(self.center) + np.array([self.pan_x, self.pan_y, 0.0])
        eye = target + self._direction() * self.distance
        return Matrix44.look_at(eye, target, np.array([0.0, 1.0, 0.0]))

    def view_axes(self):
        """Ejes de la cámara en coordenadas mundo: (derecha, arriba, hacia el observador).
        Sirve para que el ViewCube refleje la orientación actual."""
        z = self._direction()
        x = np.cross([0.0, 1.0, 0.0], z)
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        return x, y, z

    def rotate(self, dx, dy):
        self.rotation_y += dx * self.rotation_speed
        self.rotation_y = (self.rotation_y + np.pi) % (2 * np.pi) - np.pi
        self.rotation_x += dy * self.rotation_speed
        self.rotation_x = np.clip(self.rotation_x, -PITCH_LIMIT, PITCH_LIMIT)

    def pan(self, dx, dy):
        forward = self._direction()
        right = np.cross(forward, [0.0, 1.0, 0.0])
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        up /= np.linalg.norm(up)
        self.center = self.center + (dx * right + dy * up) * (self.pan_speed * self.distance)

    def zoom(self, amount):
        self.distance *= 1.0 - amount * self.zoom_speed
        self.distance = np.clip(self.distance, self.radius * 0.05, self.radius * 10.0)

    def set_model_bounds(self, center, radius):
        """Update the model center and radius for the camera"""
        self.center = np.array(center, dtype=float)
        self._home_center = self.center.copy()
        self.radius = radius
        self.distance = np.clip(self.distance, radius * 0.5, radius * 5.0)