import random
from ragtimerumble.config import DIRECTION_TO_SIDE, DIRECTIONS
from ragtimerumble.io import load_skin, image_mirror


class SpriteSheet:
    def __init__(self, data, start_animation='idle'):
        self.data = data
        self.animation = start_animation
        self.index = random.randrange(0, self.animation_length() - 1)
        self.images = load_skin(data)

    @property
    def exposures(self):
        return self.data['animations'][self.animation]['exposures']

    def image(self, direction=DIRECTIONS.RIGHT, variation=0):
        index = image_index_from_exposures(self.index, self.exposures)
        index += self.data['animations'][self.animation]['startframe']
        side = DIRECTION_TO_SIDE[direction]
        self.images[variation]
        self.images[variation][side]
        image = self.images[variation][side][index]
        flipped = direction in DIRECTIONS.FLIPPED
        return image_mirror(image, horizontal=True) if flipped else image

    def animation_length(self):
        return sum(self.exposures)

    @property
    def animation_is_done(self):
        return self.index >= sum(self.exposures) - 1

    def restart(self):
        self.index = 0

    def __next__(self):
        if not self.animation_is_done:
            self.index += 1


def image_index_from_exposures(index, exposures):
    """Data indexes:
    0       1   2           3           4
    Animation indexes:
    0 - 1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9
    Return examples:
        index = 1 -> 2
        index = 3 -> 6
        index = 8 -> 3
    """
    loop = 0
    for i, d in enumerate(exposures):
        for _ in range(d):
            if index == loop:
                return i
            loop += 1
    return 0
