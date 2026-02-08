from PySide6 import QtCore


def get_stair_line(rect, inclination):
    mult = rect.width()
    x = rect.left()
    y = rect.center().y() - (mult * (inclination / 2))
    p1 = QtCore.QPointF(x, y)
    x = rect.right()
    y = rect.center().y() - (mult * (-inclination / 2))
    p2 = QtCore.QPointF(x, y)
    line = QtCore.QLineF(p1, p2)
    offset = rect.center().y() - line.center().y()
    line.setP1(QtCore.QPointF(rect.left(), p1.y() + offset))
    line.setP2(QtCore.QPointF(rect.right(), p2.y() + offset))
    return line


def is_zone(data):
    return False if len(data) != 4 else all(isinstance(n, int) for n in data)


def is_point(data):
    if len(data) != 2:
        return False
    return all(isinstance(n, (int, float)) for n in data)


def get_interaction_text(interaction):
    if interaction['direction'] == 'left':
        return f"<- {interaction['action']}"
    if interaction['direction'] == 'right':
        return f"{interaction['action']} ->"
    if interaction['direction'] == 'up':
        return f"^\n{interaction['action']}"
    if interaction['direction'] == 'down':
        return f"{interaction['action']}\nv"

