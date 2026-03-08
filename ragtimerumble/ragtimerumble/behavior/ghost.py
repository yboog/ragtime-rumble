import random
from ragtimerumble.io import load_data, play_sound
from ragtimerumble.sprite import SpriteSheet
from ragtimerumble.config import COUNTDOWNS, DIRECTIONS, SPEED
from ragtimerumble.mathutils import is_vertical_segment
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.pathfinding import (
    shortest_path, points_to_direction, distance, random_position_in_rect)


class Ghost:
    def __init__(
            self, file=None, startposition=None, scene=None,
            direction=None, blendmode='normal', zone=None, **_):
        self.data = load_data(file)
        self.scene = scene
        self.zone = zone
        self.speed = SPEED.GHOST_MIN
        self.startposition = startposition
        self.coordinates = Coordinates((startposition))
        self.spritesheet = SpriteSheet(self.data, 'idle')
        self.direction = direction or DIRECTIONS.LEFT
        self.blendmode = blendmode
        self.destination = None
        self.walk_cooldown = random.choice(
            range(COUNTDOWNS.GHOST_WALK_COUNT_DOWN_MIN,
                  COUNTDOWNS.GHOST_WALK_COUNT_DOWN_MAX))

    @property
    def image(self):
        return self.spritesheet.image(self.direction)

    @property
    def render_position(self):
        offset_x, offset_y = self.spritesheet.data['center']
        return self.coordinates.x - offset_x, self.coordinates.y - offset_y

    @property
    def switch(self):
        return self.data['y'] + self.coordinates.y

    def start_walk(self):
        self.coordinates.round()
        dst = random_position_in_rect(self.zone, self.coordinates.position)
        self.path = iter(shortest_path(self.coordinates.position, dst))
        self.spritesheet.animation = 'walk'
        self.destination = next(self.path)
        self.spritesheet.index = 1
        self.speed = random.choice(
            range(int(SPEED.GHOST_MIN * 100),
                  int(SPEED.GHOST_MAX * 100))) / 100
        self.walk()

    def walk(self):
        p1 = self.coordinates.position
        direction = points_to_direction(p1, self.destination)
        if not direction:
            self.destination = next(self.path)
            return self.walk()
        p2 = self.coordinates.shift(direction, self.speed, 0)
        if not is_vertical_segment(p1, p2):
            if p2[0] > p1[0]:
                self.direction = DIRECTIONS.RIGHT
            else:
                self.direction = DIRECTIONS.LEFT

        if distance(p1, self.destination) < distance(p2, self.destination):
            self.spritesheet.animation = 'idle'
            self.spritesheet.index = 0
            self.walk_cooldown = random.choice(
                range(COUNTDOWNS.GHOST_WALK_COUNT_DOWN_MIN,
                    COUNTDOWNS.GHOST_WALK_COUNT_DOWN_MAX))

        self.coordinates.position = p2
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def __next__(self):
        self.walk_cooldown = max((0, self.walk_cooldown - 1))
        if self.walk_cooldown:
            next(self.spritesheet)
            return

        if self.spritesheet.animation in 'idle':
            if self.spritesheet.animation_is_done:
                return self.start_walk()
        if self.spritesheet.animation in ('walk', 'runcycle'):
            return self.walk()
        next(self.spritesheet)


