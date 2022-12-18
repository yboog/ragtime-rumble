from drunkparanoia.coordinates import Coordinates


class Background:
    def __init__(self, image, position):
        self.position = position
        self.image = image


class Overlay:
    def __init__(self, image, position, y):
        self.image = image
        self.switch = y
        self.render_position = position
        self.coordinates = Coordinates(position)


class Prop:
    def __init__(self, image, position, center, box, scene):
        self.coordinates = Coordinates(position)
        self.center = center
        self.image = image
        self.scene = scene
        self.box = box

    @property
    def render_position(self):
        offset_x, offset_y = self.center
        return self.coordinates.x - offset_x, self.coordinates.y - offset_y

    @property
    def screen_box(self):
        if self.box is None:
            return
        box = self.box[:]
        box[0] += self.coordinates.x
        box[1] += self.coordinates.y
        return box
