import math
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

    def shift(self, direction, speed):
        vector = DIRECTION_TO_VECTOR[direction]
        if vector[0] != 0 and vector[1] != 0:
            # This is the vector(1, 1) lenght to ensure the character doesn't
            # go fester in diagonal than straight directions
            speed /= 1.41421
        return self.x + vector[0] * speed, self.y + vector[1] * speed

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