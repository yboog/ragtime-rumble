
from ragtimerumble.coordinates import Coordinates, box_hit_box
from ragtimerumble.io import load_data, play_sound
from ragtimerumble.sprite import SpriteSheet


class SaloonDoor:

    def __init__(self, scene, file, position, switch, zone, **_):
        self.data = load_data(file)
        self.scene = scene
        self.switch = switch
        self.spritesheet = SpriteSheet(self.data, 'closed')
        self.coordinates = Coordinates((position))
        self.zone = zone

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def image(self):
        return self.spritesheet.image()

    def __next__(self):
        char_in_zone = any(
            box_hit_box(self.zone, c.screen_box)
            for c in self.scene.characters)
        match self.spritesheet.animation :
            case 'closed':
                if char_in_zone:
                    self.open(play_door_sound=True)
                else:
                    self.spritesheet.index = 0
            case 'closing':
                if char_in_zone and self.spritesheet.index > 15:
                    self.open(play_door_sound=self.spritesheet.index > 25)
                elif char_in_zone:
                    self.spritesheet.index = 0
        next(self.spritesheet)

    def open(self, play_door_sound=False):
        if play_door_sound:
            play_sound('/resources/sounds/saloon-door-slam.wav')
        self.spritesheet.animation = 'closing'
        self.spritesheet.index = 0


