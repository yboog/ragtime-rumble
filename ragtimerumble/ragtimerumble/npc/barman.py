import random
import itertools

from ragtimerumble.config import COUNTDOWNS
from ragtimerumble.config import SPEED
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data
from ragtimerumble.pathfinding import points_to_direction, distance
from ragtimerumble.sprite import SpriteSheet


class Barman:

    def __init__(self, file=None, startposition=None, path=None, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'idle')
        self.coordinates = Coordinates((startposition))
        self.idle_cooldown = random.randint(
            *COUNTDOWNS.BARMAN_IDLE_COOLDOWN_RANGE)
        self.walk_cooldown = 0
        self.path = itertools.cycle(path)
        self.destination = next(self.path)

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return self.data['y']

    @property
    def image(self):
        return self.spritesheet.image()

    def walk(self):
        self.walk_cooldown -= 1
        p1 = self.coordinates.position
        direction = points_to_direction(p1, self.destination)
        if not direction:
            self.destination = next(self.path)
            return self.walk()
        p2 = self.coordinates.shift(direction, SPEED.BARMAN, 0)
        if distance(p1, self.destination) < distance(p2, self.destination):
            self.destination = next(self.path)
            return self.walk()

        self.coordinates.position = p2
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def __next__(self):

        if self.walk_cooldown > 0 and self.spritesheet.animation == 'walk':
            self.walk()
            return

        idles = 'towel', 'idle'
        anim = self.spritesheet.animation
        if anim in idles and self.idle_cooldown > 0:
            self.idle_cooldown -= 1
            if self.spritesheet.animation_is_done:
                self.spritesheet.index = 0
            next(self.spritesheet)
            return

        if anim == 'towel':
            self.spritesheet.animation = 'towel-end'
            self.spritesheet.index = 0
            return

        if anim == 'towel-end' and not self.spritesheet.animation_is_done:
            next(self.spritesheet)
            return

        if anim == 'towel-start':
            if not self.spritesheet.animation_is_done:
                next(self.spritesheet)
                return
            self.idle_cooldown = random.randint(
                *COUNTDOWNS.BARMAN_IDLE_COOLDOWN_RANGE)
            self.spritesheet.animation = 'towel'
            self.spritesheet.index = 0
            return

        # Set new behavior
        match random.choice(('towel', 'idle', 'walk')):
            case 'towel':
                self.spritesheet.animation = 'towel-start'
                self.spritesheet.index = 0
                return
            case 'idle':
                self.idle_cooldown = random.randint(
                    *COUNTDOWNS.BARMAN_IDLE_COOLDOWN_RANGE)
                self.spritesheet.animation = 'idle'
                self.spritesheet.index = 0
                return
            case 'walk':
                self.spritesheet.animation = 'walk'
                self.spritesheet.index = 0
                self.walk_cooldown = random.randint(
                    *COUNTDOWNS.BARMAN_WALK_COOLDOWN_RANGE)

        next(self.spritesheet)

