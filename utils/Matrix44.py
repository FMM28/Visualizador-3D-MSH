import numpy as np

def normalize(vec):
    return (vec.T  / np.sqrt(np.sum(vec**2,axis=-1))).T

def look_at(eye, target, up, dtype=None):

    eye = np.asarray(eye)
    target = np.asarray(target)
    up = np.asarray(up)

    forward = normalize(target - eye)
    side = normalize(np.cross(forward, up))
    up = normalize(np.cross(side, forward))

    return np.array((
            (side[0], up[0], -forward[0], 0.),
            (side[1], up[1], -forward[1], 0.),
            (side[2], up[2], -forward[2], 0.),
            (-np.dot(side, eye), -np.dot(up, eye), np.dot(forward, eye), 1.0)
        ), dtype=dtype)
    
def perspective_projection(fovy, aspect, near, far, dtype=None):

    ymax = near * np.tan(fovy * np.pi / 360.0)
    xmax = ymax * aspect
    return create_perspective_projection_from_bounds(-xmax, xmax, -ymax, ymax, near, far, dtype=dtype)

def create_perspective_projection_from_bounds(left,right,bottom,top,near,far,dtype=None):

    A = (right + left) / (right - left)
    B = (top + bottom) / (top - bottom)
    C = -(far + near) / (far - near)
    D = -2. * far * near / (far - near)
    E = 2. * near / (right - left)
    F = 2. * near / (top - bottom)

    return np.array((
        (  E, 0., 0., 0.),
        ( 0.,  F, 0., 0.),
        (  A,  B,  C,-1.),
        ( 0., 0.,  D, 0.),
    ), dtype=dtype)