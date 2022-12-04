from drunkparanoia.config import DIRECTIONS
from drunkparanoia.joystick import get_pressed_direction
from drunkparanoia.config import DIRECTION_TO_VECTOR, LOOPING_ANIMATIONS


class Coordinates:
    def __init__(self, position):
        self.x, self.y = position

    def shift(self, direction, speed):
        if not speed:
            return
        vector = DIRECTION_TO_VECTOR[direction]
        if vector[0] != 0 and vector[1] != 0:
            speed *= 0.75
        self.x += vector[0] * speed
        self.y += vector[1] * speed


class Player:
    def __init__(self, character, joystick):
        self.character = character
        self.joystick = joystick

    def __next__(self):
        direction = get_pressed_direction(self.joystick)
        if direction:
            self.character.direction = direction
            self.character.accelerate()
        else:
            self.character.decelerate()
        next(self.character)


class Character:
    def __init__(self, position, spritesheet):
        self.spritesheet = spritesheet
        self.coorinates = Coordinates(position)
        self.direction = DIRECTIONS.DOWN
        self.speed = 0

    @property
    def render_position(self):
        offset_x, offset_y = self.spritesheet.data['center']
        return self.coorinates.x - offset_x, self.coorinates.y - offset_y

    @property
    def image(self):
        return self.spritesheet.image(self.direction)

    def __next__(self):
        if self.speed:
            self.coorinates.shift(self.direction, self.speed)
        if self.spritesheet.animation_is_done:
            if self.spritesheet.animation in LOOPING_ANIMATIONS:
                self.spritesheet.restart()
                return
            self.spritesheet.animation = 'idle'
            return
        next(self.spritesheet)

    def accelerate(self):
        if self.speed == 0:
            self.speed = .2
            self.start()
            return
        self.speed = min((self.speed * 1.2, 2))

    def decelerate(self):
        if self.speed == 0:
            return
        self.speed /= 1.2
        if self.speed < .2:
            self.speed = 0
            self.stop()

    def start(self):
        self.spritesheet.animation = 'walk'
        self.spritesheet.index = 0

    def stop(self):
        self.spritesheet.animation = 'idle'
        self.spritesheet.index = 0