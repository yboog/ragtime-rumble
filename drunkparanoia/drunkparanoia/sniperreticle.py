
from drunkparanoia.coordinates import (
    Coordinates, clamp_to_zone, point_in_rectangle)
from drunkparanoia.config import (
    SPEED, CHARACTER_STATUSES, COUNTDOWNS)
from drunkparanoia.joystick import get_pressed_direction
from drunkparanoia.io import play_sound


class SniperReticle:

    def __init__(self, rect, scene):
        self.player = None
        self.rect = rect
        self.coordinates = Coordinates(rect_center(rect))
        self.direction = None
        self.scene = scene
        self.speed = 0
        self.price = 1

    @property
    def target_characters(self):
        if not self.player:
            return []
        return [
            char for char in self.scene.characters
            if point_in_rectangle(self.coordinates.position, *char.hitbox) and
            char.status != CHARACTER_STATUSES.OUT]

    def buy(self, player):
        self.price += 1
        self.player = player

    def accelerate(self):
        if self.speed == 0:
            self.speed = SPEED.SNIPER_RECTICLE_MIN
            return
        self.speed = min((
            self.speed - (1 - SPEED.SNIPER_RECTICLE_FACTOR),
            SPEED.SNIPER_RECTICLE_MAX))

    def decelerate(self):
        if self.speed == 0:
            return
        self.speed /= SPEED.SNIPER_RECTICLE_FACTOR
        if self.speed < SPEED.SNIPER_RECTICLE_MIN:
            self.speed = 0

    def reset(self):
        self.coordinates.position = rect_center(self.rect)

    def __next__(self):
        if self.player is None:
            return
        direction = get_pressed_direction(self.player.joystick, rs=True)
        if direction:
            self.accelerate()
        else:
            self.decelerate()
        self.direction = direction or self.direction
        if not self.speed:
            return
        position = self.coordinates.shift(self.direction, self.speed, 0)
        position = clamp_to_zone(position, self.rect)
        self.coordinates.position = position

    def shoot(self):
        play_sound('resources/sounds/colt.wav')
        for character in self.target_characters:
            self.player.kill(character, silently=True, getcoin=False)
            self.player.bullet_cooldown = COUNTDOWNS.SNIPER_BULLET_COOLDOWN
        self.player = None


def rect_center(rect):
    return rect[0] + (rect[2] / 2), rect[1] + (rect[3] / 2)
