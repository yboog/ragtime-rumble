from drunkparanoia.pathfinding import (
    distance, points_to_direction, seg_to_vector, vector_to_direction)
from drunkparanoia.coordinates import offset_point


class HardPathPilot:

    def __init__(self, character, path):
        self.path = path
        self.character = character

    def __next__(self):
        if not self.path:
            raise StopIteration

        destination = self.path[0]
        origin = self.character.coordinates.position[:]
        if list(origin) == list(destination):
            self.path.pop(0)
            return

        self.character.accelerate()
        vector = seg_to_vector(origin, destination)
        speed = self.character.speed
        step = offset_point(self.character.coordinates.position, vector, speed)
        self.character.coordinates.position = step

        inclination = self.character.scene.inclination_at(step)
        direction_vector = vector[0] - inclination, vector[1]
        direction = vector_to_direction(direction_vector)
        self.character.direction = direction
        dist1 = distance(origin, self.path[0])
        dist2 = distance(self.character.coordinates.position, self.path[0])
        if dist1 < dist2:
            self.character.coordinates.position = self.path.pop(0)[:]
            return


class SmoothPathPilot:
    def __init__(self, character, path):
        self.character = character
        self.path = path

    def __next__(self):
        if not self.path:
            raise StopIteration

        origin = self.character.coordinates.position[:]
        direction = points_to_direction(origin, self.path[0])
        self.character.direction = direction or self.character.direction
        self.character.accelerate()
        self.character.offset()

        if origin == self.character.coordinates.position:
            raise StopIteration

        dist1 = distance(origin, self.path[0])
        dist2 = distance(self.character.coordinates.position, self.path[0])
        if dist1 < dist2:
            # TODO: This line lead IP's. If the pop is not assigned,
            # the character is shaking.
            position = self.path.pop(0)[:]
            if self.path:
                self.character.coordinates.position = position
