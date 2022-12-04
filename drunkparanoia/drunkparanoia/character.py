import random
from drunkparanoia.config import DIRECTIONS, SPEED, COUNTDOWNS
from drunkparanoia.joystick import get_pressed_direction, get_current_commands
from drunkparanoia.config import LOOPING_ANIMATIONS, CHARACTER_STATUSES
from drunkparanoia.coordinates import Coordinates, get_box


class Player:
    def __init__(self, character, joystick):
        self.character = character
        self.joystick = joystick

    def __next__(self):
        if self.character.status == CHARACTER_STATUSES.STUCK:
            next(self.character)
            return

        if self.character.status == CHARACTER_STATUSES.FREE:
            commands = get_current_commands(self.joystick)
            if commands.get('X'):
                self.character.stop()
                self.character.request_duel()
                return

        if self.character.status == CHARACTER_STATUSES.INTERACTING:
            next(self.character)
            return

        direction = get_pressed_direction(self.joystick)
        if direction:
            self.character.direction = direction
            self.character.accelerate()
        else:
            self.character.decelerate()
        next(self.character)


class Npc:
    # TODO
    def __init__(self, character):
        self.character = character
        self.coma_count_down = random.randrange(
            COUNTDOWNS.COMA_MIN, COUNTDOWNS.COMA_MAX)

    def __next__(self):
        next(self.character)
        if self.character.status == CHARACTER_STATUSES.FREE:
            self.coma_count_down -= 1


class Character:
    def __init__(self, position, spritesheet, scene):
        self.spritesheet = spritesheet
        self.coordinates = Coordinates(position)
        self.direction = DIRECTIONS.DOWN
        self.speed = 0
        self.scene = scene
        self.vomit_count_down = random.randrange(
            COUNTDOWNS.VOMIT_MIN, COUNTDOWNS.VOMIT_MAX)
        self.status = CHARACTER_STATUSES.FREE

    @property
    def box(self):
        return self.spritesheet.data['box'][:]

    @property
    def screen_box(self):
        box = self.box
        box[0] += self.coordinates.x
        box[1] += self.coordinates.y
        return get_box(self.coordinates.position, self.box)

    @property
    def render_position(self):
        offset_x, offset_y = self.spritesheet.data['center']
        return self.coordinates.x - offset_x, self.coordinates.y - offset_y

    @property
    def image(self):
        return self.spritesheet.image(self.direction)

    def offset(self):
        position = self.coordinates.shift(self.direction, self.speed)
        box = get_box(position, self.box)
        if not self.scene.collide_prop(box):
            self.coordinates.x = position[0]
            self.coordinates.y = position[1]
            return
        if self.direction not in DIRECTIONS.DIAGONALS:
            return
        box = get_box((self.coordinates.x, position[1]), self.box)
        if not self.scene.collide_prop(box):
            self.coordinates.y = position[1]
            return
        box = get_box((position[0], self.coordinates.y), self.box)
        if not self.scene.collide_prop(box):
            self.coordinates.x = position[0]

    def vomit(self):
        self.stop()
        self.spritesheet.animation = 'vomit'
        self.spritesheet.index = 0
        self.vomit_count_down = random.randrange(
            COUNTDOWNS.VOMIT_MIN, COUNTDOWNS.VOMIT_MAX)
        self.status = CHARACTER_STATUSES.STUCK

    def __next__(self):
        match self.status:
            case CHARACTER_STATUSES.STUCK:
                if self.spritesheet.animation_is_done:
                    self.status = CHARACTER_STATUSES.FREE
                    self.stop()
                    return
                next(self.spritesheet)
                return

            case CHARACTER_STATUSES.INTERACTING:
                if self.spritesheet.animation_is_done:
                    if self.spritesheet.animation == 'call':
                        self.spritesheet.animation = 'smoke'
                        self.spritesheet.index = 0
                    elif self.spritesheet.animation == 'smoke':
                        self.status = CHARACTER_STATUSES.FREE
                        self.spritesheet.animation = 'idle'
                        self.spritesheet.index = 0
                    return
                next(self.spritesheet)
                return

        if self.status == CHARACTER_STATUSES.FREE:
            self.vomit_count_down -= 1

        if self.vomit_count_down <= 0:
            self.vomit()
            return

        if self.speed:
            self.offset()

        if self.spritesheet.animation_is_done:
            if self.spritesheet.animation in LOOPING_ANIMATIONS:
                self.spritesheet.restart()
                return
            self.spritesheet.animation = 'idle'
            return
        next(self.spritesheet)

    def accelerate(self):
        if self.speed == 0:
            self.start()
            return
        self.speed = min((self.speed * SPEED.FACTOR, SPEED.MAX))

    def decelerate(self):
        if self.speed == 0:
            return
        self.speed /= SPEED.FACTOR
        if self.speed < SPEED.MIN:
            self.stop()

    def start(self):
        self.speed = SPEED.MIN
        self.spritesheet.animation = 'walk'
        self.spritesheet.index = 0

    def stop(self):
        self.speed = 0
        self.spritesheet.animation = 'idle'
        self.spritesheet.index = 0

    def request_duel(self):
        for origin, target in self.scene.possible_duels:
            if origin != self:
                continue

        self.status = CHARACTER_STATUSES.INTERACTING
        self.spritesheet.animation = 'call'
        self.spritesheet.index = 0