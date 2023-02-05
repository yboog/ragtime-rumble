import math
from matplotlib.path import Path
from drunkparanoia.config import DIRECTION_TO_VECTOR


class Coordinates:
    def __init__(self, position):
        self.x, self.y = position

    @property
    def position(self):
        return self.x, self.y

    @position.setter
    def position(self, position):
        self.x, self.y = position

    def shift(self, direction, speed, inclination):
        vector = list(DIRECTION_TO_VECTOR[direction])
        vector[1] = vector[1] + (inclination * vector[0])
        return offset_point((self.x, self.y), vector, speed)

    def distance_to(self, coordinates):
        return distance(self.position, coordinates.position)


def get_box(position, box):
    box = box[:]
    box[0] += position[0]
    box[1] += position[1]
    return box


def box_hit_box(box1, box2):
    return (
        box1[0] + box1[2] >= box2[0] and
        box1[0] <= box2[0] + box2[2] and
        box1[1] + box1[3] >= box2[1] and
        box1[1] <= box2[1] + box2[3])


def distance(p1, p2):
    (ax, ay), (bx, by) = p1, p2
    return math.sqrt(
        (bx - ax)**2 +
        (by - ay)**2)


def point_in_rectangle(p, left, top, width, height):
    x, y = p
    return left <= x <= left + width and top <= y <= top + height


def box_hit_polygon(rect, polygon):
    tl = [rect[0], rect[1]]
    tr = [rect[0] + rect[2], rect[1]]
    bl = [rect[0], rect[1] + rect[3]]
    br = [rect[0] + rect[2], rect[1] + rect[3]]
    rect = (tl, tr, bl, br)
    rect_path = Path(rect)
    polygon_path = Path(polygon)
    return rect_path.intersects_path(polygon_path, filled=True)


def path_cross_polygon(path, polygon):
    return Path(path).intersects_path(Path(polygon))


def path_cross_rect(path, rect):
    tl = [rect[0], rect[1]]
    tr = [rect[0] + rect[2], rect[1]]
    bl = [rect[0], rect[1] + rect[3]]
    br = [rect[0] + rect[2], rect[1] + rect[3]]
    path = Path(path)
    path2 = Path([tl, tr, bl, br])
    return path.intersects_path(path2)


def norm(vector):
    return [n / math.sqrt(vector[0]**2 + vector[1]**2) for n in vector]


def offset_point(point, vector, distance):
    v_norm = norm(vector)
    return [point[0] + distance * v_norm[0], point[1] + distance * v_norm[1]]
