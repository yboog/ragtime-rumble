import random
from drunkparanoia.config import HAT_TO_DIRECTION
from drunkparanoia.coordinates import distance, get_box, point_in_rectangle


def points_to_direction(p1, p2):
    x = round(p1[0] - p2[0], 1)
    x = -1 if x > 0 else 1 if x < 0 else 0
    y = round(p1[1] - p2[1], 1)
    y = -1 if y > 0 else 1 if y < 0 else 0
    return HAT_TO_DIRECTION.get((x, y))


def equilateral_path(origin, dst):
    dst = list(dst)[:]
    dst[0] = dst[0] if dst[0] is not None else origin[0]
    dst[1] = dst[1] if dst[1] is not None else origin[1]
    if origin[0] in dst or origin[1] in dst:
        return [dst]
    intermediate = random.choice((
        [origin[0], dst[1]],
        [dst[0], origin[1]]))
    return [intermediate, dst]


def filter_close_paths(point, paths, maxdistance):
    return [path for path in paths if distance(point, path[0]) < maxdistance]


def smooth_path_to_path(orig, points):
    path = []
    for point in points:
        path.extend(shortest_path(orig, point))
        orig = point
    return path


def shortest_path(orig, dst):
    """
    Create a path between an origin and a destination lock to height
    directions. Function can contains some random to decide the way to use.
            ORIG------------- OTHER WAY POSSIBLE
                \            \
                 \------------ DST
            INTERMEDIATE
    """
    dst = list(dst)[:]
    dst[0] = dst[0] if dst[0] is not None else orig[0]
    dst[1] = dst[1] if dst[1] is not None else orig[1]

    if orig[0] in dst or orig[1] in dst:
        return [dst]

    reverse = random.choice([True, False])
    if reverse:
        orig, dst = dst, orig

    equi1 = dst[0], orig[1]
    equi2 = orig[0], dst[1]
    dist1 = distance(orig, equi1)
    dist2 = distance(orig, equi2)
    if dist1 > dist2:
        if dst[0] > orig[0]:
            intermediate = (equi2[0] + dist2, equi2[1])
        else:
            intermediate = (equi2[0] - dist2, equi2[1])
    else:
        if dst[1] > orig[1]:
            intermediate = (equi1[0], equi1[1] + dist1)
        else:
            intermediate = (equi1[0], equi1[1] - dist1)
    if reverse:
        orig, dst = dst, orig
    return [intermediate, dst]


def choice_destination(scene, position, box):
    limit = 0
    while True:
        dst = scene.choice_destination_from(position)
        if dst is None:
            break
        if not scene.collide(get_box(dst, box)):
            return dst
        limit += 1

    x, y = [int(n) for n in position]
    x = random.randrange(x - 75, x + 75)
    y = random.randrange(y - 75, y + 75)
    pos = x, y
    while scene.collide(get_box(pos, box)):
        x, y = [int(n) for n in position]
        x = random.randrange(x - 75, x + 75)
        y = random.randrange(y - 75, y + 75)
        pos = x, y
    return pos


def choce_destination_from(targets, point):
    targets = [
        t for t in targets if point_in_rectangle(point, *t['origin'])]

    if not targets:
        return

    destinations = [
        d for t in targets
        for _ in range(t['weight'])
        for d in t['destinations']]

    destination = random.choice(destinations)
    x = random.randrange(destination[0], destination[0] + destination[2])
    y = random.randrange(destination[1], destination[1] + destination[3])
    return x, y
