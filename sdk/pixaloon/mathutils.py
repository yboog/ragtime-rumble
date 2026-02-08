import math


def distance(p1, p2):
    (ax, ay), (bx, by) = p1, p2
    return math.sqrt(
        (bx - ax)**2 +
        (by - ay)**2)


def start_end_to_rect_data(start, end):
    x = min((start[0], end[0]))
    y = min((start[1], end[1]))
    w = max((start[0], end[0])) - x
    h = max((start[1], end[1])) - y
    return x, y, w, h

