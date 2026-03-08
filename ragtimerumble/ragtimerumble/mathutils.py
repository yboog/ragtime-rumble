

import math


def norm_vector(vec):
    norm = math.sqrt(sum(x**2 for x in vec))
    return [x / norm for x in vec]


def set_vector_length(v, length):
    x, y = v
    norm = math.sqrt(x*x + y*y)

    if norm == 0:
        raise ValueError("Impossible de redimensionner un vecteur nul")

    scale = length / norm
    return (x * scale, y * scale)


def get_vector(p1, p2, norm=True):
    vec = [p2[0] - p1[0], p2[1] - p1[1]]
    if norm:
        return norm_vector(vec)
    return vec


def is_vertical_segment(p1, p2):
    v = get_vector(p1, p2)
    return -0.01 < v[0] < 0.01