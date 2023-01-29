from drunkparanoia.config import DIRECTIONS, CHARACTER_STATUSES, DUEL
from drunkparanoia.coordinates import path_cross_rect


def find_possible_duels(scene):
    characters = scene.characters
    possible_duels = []
    for char1 in characters:
        if char1.status not in CHARACTER_STATUSES.DUELABLES:
            continue
        duel = None
        duel_distance = None

        for char2 in characters:
            if char2.status not in CHARACTER_STATUSES.DUELABLES:
                continue
            if char1 == char2:
                continue

            height = char1.coordinates.y - char2.coordinates.y
            if abs(height) > DUEL.TOLERENCE:
                continue

            x1 = char1.coordinates.x
            x2 = char2.coordinates.x
            path = char1.coordinates.position, char2.coordinates.position
            conditions = (
                char1.direction in DIRECTIONS.RIGHTS and (x1 - x2) > 0 or
                char1.direction in DIRECTIONS.LEFTS and (x2 - x1) > 0 or
                not (DUEL.RANGE[0] <= abs(x1 - x2) <= DUEL.RANGE[1]) or
                any(path_cross_rect(path, fence) for fence in scene.fences))

            if conditions:
                continue

            dist = char1.coordinates.distance_to(char2.coordinates)
            if duel_distance and dist > duel_distance:
                continue
            duel = (char1, char2)
            duel_distance = dist

        if duel is not None:
            possible_duels.append(duel)

    return possible_duels
