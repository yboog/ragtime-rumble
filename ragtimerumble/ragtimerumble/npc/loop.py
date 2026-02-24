
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data
from ragtimerumble.sprite import SpriteSheet


class Loop:
    def __init__(self, file, position, switch, **_):
        self.data = load_data(file)
        self.switch = switch
        self.spritesheet = SpriteSheet(self.data, 'loop')
        self.coordinates = Coordinates((position))

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def image(self):
        return self.spritesheet.image()

    def __next__(self):
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)
