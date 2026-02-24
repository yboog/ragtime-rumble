import random

from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data
from ragtimerumble.sprite import SpriteSheet


class Pianist:
    slows = [
        'slow1',
        'slow2',
        'slow3',
        'slow4']
    fasts = [
        'fast1',
        'fast2',
        'fast3',
        'fast4']

    def __init__(self, file='', startposition=None, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'slow1')
        self.coordinates = Coordinates((startposition))
        self.sequence = []

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return self.data['y']

    def next_animation(self):
        if not self.sequence:
            slow = random.choice((False, True))
            if slow:
                return random.choice(self.slows)
            self.sequence = [
                random.choice(self.fasts),
                random.choice(self.fasts)]
        return self.sequence.pop()

    def __next__(self):
        if self.spritesheet.animation_is_done:
            self.spritesheet.animation = self.next_animation()
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    @property
    def image(self):
        return self.spritesheet.image()


