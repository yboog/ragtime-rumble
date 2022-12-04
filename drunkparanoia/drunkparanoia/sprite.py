from drunkparanoia.config import DIRECTION_TO_SIDE, FLIPPED_DIRECTIONS
from drunkparanoia.io import load_skin, image_mirror


class SpriteSheet:
    def __init__(self, data):
        self.data = data
        self.animation = 'idle'
        self.index = 0
        self.images = load_skin(data)

    @property
    def durations(self):
        return self.data['animations'][self.animation]['durations']

    def image(self, direction):
        index = image_index_from_durations(self.index, self.durations)
        index += self.data['animations'][self.animation]['startframe']
        side = DIRECTION_TO_SIDE[direction]
        image = self.images[side][index]
        flipped = direction in FLIPPED_DIRECTIONS
        return image_mirror(image, horizontal=True) if flipped else image

    def animation_length(self):
        return sum(self.data['animations'][self.animation]['durations'])

    @property
    def animation_is_done(self):
        return self.index >= sum(self.durations)

    def restart(self):
        self.index = 0

    def __next__(self):
        if not self.animation_is_done:
            self.index += 1


def image_index_from_durations(index, durations):
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
    for i, d in enumerate(durations):
        for _ in range(d):
            if index == loop:
                return i
            loop += 1
    return 0
