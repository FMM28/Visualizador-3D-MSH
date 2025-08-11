from pyrr import Matrix44, Vector3
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
        self.pan_speed = 0.005
        
    def get_view_matrix(self):
        eye = Vector3([
            self.distance * np.cos(self.rotation_y) * np.cos(self.rotation_x),
            self.distance * np.sin(self.rotation_x),
            self.distance * np.sin(self.rotation_y) * np.cos(self.rotation_x)
        ])
        
        target = Vector3([
            self.center[0] + self.pan_x,
            self.center[1] + self.pan_y,
            self.center[2]
        ])
        
        return Matrix44.look_at(
            eye.xyz + target.xyz,
            target.xyz,
            (0.0, 1.0, 0.0)
        )
    
    def rotate(self, dx, dy):
        self.rotation_y += dx * self.rotation_speed
        self.rotation_x += dy * self.rotation_speed
        self.rotation_x = np.clip(self.rotation_x, -np.pi/2 + 0.01, np.pi/2 - 0.01)
    
    def pan(self, dx, dy):
        self.pan_x += dx * self.pan_speed * self.distance
        self.pan_y += dy * self.pan_speed * self.distance
    
    def zoom(self, amount):
        self.distance *= 1.0 - amount * self.zoom_speed
        self.distance = np.clip(self.distance, self.radius * 0.5, self.radius * 10.0)