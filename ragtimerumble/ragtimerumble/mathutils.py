

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