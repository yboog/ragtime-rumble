import sys
import random
import itertools

from ragtimerumble.config import (
    COUNTDOWNS, DIRECTIONS, DOG_GROWL_DISTANCE, DOG_BARK_DISTANCE)
from ragtimerumble.config import CHARACTER_STATUSES, SPEED
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data, image_mirror, play_sound
from ragtimerumble.pathfinding import points_to_direction, distance
from ragtimerumble.sprite import SpriteSheet


class Dog:
    def __init__(
            self, scene=None, file=None, startposition=None,
            path=None, direction=None, **_):
        self.data = load_data(file)
        self.scene = scene
        self.spritesheet = SpriteSheet(self.data, 'sit')
        self.coordinates = Coordinates((startposition))
        self.behavior_cooldown = random.randint(
            *COUNTDOWNS.DOG_IDLE_COOLDOWN_RANGE)
        self.path = itertools.cycle(path)
        self.destination = next(self.path)
        self.direction = direction

    def closest_player_distance(self):
        distance = sys.maxsize
        for player in self.scene.players:
            if player.dying or player.dead:
                continue
            if player.character.status == CHARACTER_STATUSES.INTERACTING:
                continue
            coordinates = player.character.coordinates
            distance = min((
                distance,
                self.coordinates.distance_to(coordinates)))
        return distance

    @property
    def render_position(self):
        offset_x, offset_y = self.spritesheet.data['center']
        return self.coordinates.x - offset_x, self.coordinates.y - offset_y

    @property
    def switch(self):
        return self.coordinates.y

    @property
    def image(self):
        if self.direction not in DIRECTIONS.FLIPPED:
            return image_mirror(self.spritesheet.image(), horizontal=True)
        return self.spritesheet.image()

    def walk(self):
        self.behavior_cooldown -= 1
        p1 = self.coordinates.position
        direction = points_to_direction(p1, self.destination)
        if not direction:
            self.destination = next(self.path)
            return self.walk()
        self.direction = direction
        p2 = self.coordinates.shift(direction, SPEED.DOG, 0)
        if distance(p1, self.destination) < distance(p2, self.destination):
            self.destination = next(self.path)
            return self.walk()

        self.coordinates.position = p2
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def __next__(self):

        animation = self.spritesheet.animation
        if animation == 'bark' and not self.spritesheet.animation_is_done:
            next(self.spritesheet)
            return

        distance = self.closest_player_distance()
        if 0 < distance < DOG_BARK_DISTANCE:
            if animation == 'bark' and not self.spritesheet.animation_is_done:
                next(self.spritesheet)
                return
            play_sound('resources/sounds/barkling.wav')
            self.spritesheet.animation = 'bark'
            self.spritesheet.index = 0
            return
        elif DOG_BARK_DISTANCE < distance < DOG_GROWL_DISTANCE:
            if animation in ('bark', 'growl'):
                if not self.spritesheet.animation_is_done:
                    next(self.spritesheet)
                    return
            play_sound('resources/sounds/growling.wav')
            self.spritesheet.animation = 'growl'
            self.spritesheet.index = 0
            return

        if self.behavior_cooldown > 0 and animation == 'siderun':
            self.walk()
            return

        idles = 'sit', 'idle'
        if self.behavior_cooldown > 0 and animation in idles:
            self.behavior_cooldown -= 1
            if self.spritesheet.animation_is_done:
                self.spritesheet.index = 0
                return
            next(self.spritesheet)
            return

        if self.behavior_cooldown == 0 and animation == 'siderun':
            self.behavior_cooldown = random.randint(
                *COUNTDOWNS.DOG_IDLE_COOLDOWN_RANGE)
            self.spritesheet.animation = random.choice(idles)
            self.spritesheet.index = 0
            next(self.spritesheet)
            return

        if self.behavior_cooldown == 0 and animation in idles:
            self.behavior_cooldown = random.randint(
                *COUNTDOWNS.DOG_WALK_COOLDOWN_RANGE)
            self.spritesheet.animation = 'siderun'
            self.spritesheet.index = 0
            next(self.spritesheet)
            return

        if animation in ('bark', 'growl'):
            if not self.spritesheet.animation_is_done:
                next(self.spritesheet)
                return
            self.spritesheet.animation = random.choice(('sit', 'idle'))
            self.spritesheet.index = 0

        next(self.spritesheet)

