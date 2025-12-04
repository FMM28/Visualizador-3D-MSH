import utils.Matrix44 as Matrix44
import numpy as np

class Camera:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.reset()
        
    def reset(self):
        self.distance = self.radius * 2.5
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom_speed = 0.1
        self.rotation_speed = 0.01
        self.pan_speed = 0.001
        
    def get_view_matrix(self):
        target = np.array(self.center) + np.array([self.pan_x, self.pan_y, 0.0])

        direction = np.array([
            np.cos(self.rotation_y) * np.cos(self.rotation_x),
            np.sin(self.rotation_x),
            np.sin(self.rotation_y) * np.cos(self.rotation_x)
        ], dtype=float)

        eye = target + direction * self.distance

        return Matrix44.look_at(eye, target, np.array([0.0, 1.0, 0.0]))
    
    def rotate(self, dx, dy):
        self.rotation_y += dx * self.rotation_speed
        self.rotation_y = (self.rotation_y + np.pi) % (2 * np.pi) - np.pi
        self.rotation_x += dy * self.rotation_speed
        self.rotation_x = np.clip(self.rotation_x, -np.pi/2 + 0.01, np.pi/2 - 0.01)
    
    def pan(self, dx, dy):
        forward = np.array([
            np.cos(self.rotation_y) * np.cos(self.rotation_x),
            np.sin(self.rotation_x),
            np.sin(self.rotation_y) * np.cos(self.rotation_x)
        ], dtype=float)

        up_world = np.array([0.0, 1.0, 0.0], dtype=float)

        right = np.cross(forward, up_world)
        right = right / np.linalg.norm(right)

        up = np.cross(right, forward)
        up = up / np.linalg.norm(up)

        move = (dx * right + dy * up) * (self.pan_speed * self.distance)

        self.center = self.center + move

    def zoom(self, amount):
        self.distance *= 1.0 - amount * self.zoom_speed
        self.distance = np.clip(self.distance, self.radius * 0.05, self.radius * 10.0)
        
    def set_model_bounds(self, center, radius):
        """Update the model center and radius for the camera"""
        self.center = np.array(center)
        self.radius = radius
        self.distance = np.clip(self.distance, radius * 0.5, radius * 5.0)