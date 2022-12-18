import random
from drunkparanoia.config import (
    DIRECTIONS, SPEED, COUNTDOWNS, HAT_TO_DIRECTION, HOLDABLE_ANIMATIONS)
from drunkparanoia.joystick import get_pressed_direction, get_current_commands
from drunkparanoia.config import LOOPING_ANIMATIONS, CHARACTER_STATUSES
from drunkparanoia.coordinates import Coordinates, get_box, distance


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
            if commands.get('A'):
                self.character.stop()
                self.character.request_duel()
                return
            if commands.get('X'):
                self.character.request_interaction()
                return

        if self.character.status == CHARACTER_STATUSES.INTERACTING:
            next(self.character)
            return

        if self.character.status == CHARACTER_STATUSES.AUTOPILOT:
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
        self.cool_down = 0
        self.is_cooling_down = False

    def __next__(self):
        if self.coma_count_down == 0:
            if self.character.status != CHARACTER_STATUSES.OUT:
                self.character.status = CHARACTER_STATUSES.OUT
                self.character.spritesheet.animation = 'vomit'
                self.character.spritesheet.index = 0
                self.character.buffer_animation = 'coma'
                return
            next(self.character)
            return
        self.coma_count_down -= 1

        if self.character.status == CHARACTER_STATUSES.AUTOPILOT:
            next(self.character)
            return

        if self.character.status == CHARACTER_STATUSES.FREE:
            if self.is_cooling_down is False:
                proba = COUNTDOWNS.COOLDOWN_PROBABILITY
                do_pause = random.randrange(0, proba) == 0
                if do_pause:
                    self.character.path = None
                    self.character.ghost = None
                    self.is_cooling_down = True
                    self.cool_down = random.randrange(
                        COUNTDOWNS.COOLDOWN_MIN, COUNTDOWNS.COOLDOWN_MAX)
                    next(self.character)
                    return

            if self.cool_down == 0:
                self.character.end_autopilot()
                self.is_cooling_down = False
                self.character.status = CHARACTER_STATUSES.AUTOPILOT
                functions = [shortest_path] * 2 + [equilateral_path]
                func = random.choice(functions)
                self.character.ghost = None
                destination = self.character.choice_destination()
                position = self.character.coordinates.position
                self.character.path = func(position, destination)
                self.character.autopilot()
                next(self.character)
                return

            if self.character.speed:
                self.character.decelerate()
            self.cool_down -= 1
            next(self.character)
            return

        next(self.character)


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
        self.ghost = None
        self.path = None
        self.buffer_animation = None
        self.buffer_direction = None

    def choice_destination(self):
        limit = 0
        while True:
            # if limit < 10:
            #     raise ValueError('impossible to find dest for ', self.coordinates.position)
            dst = self.scene.choice_destination_from(self.coordinates.position)
            if dst is None:
                break
            if not self.scene.collide(get_box(dst, self.box)):
                return dst
            limit += 1
        x, y = [int(n) for n in self.coordinates.position]
        x = random.randrange(x - 75, x + 75)
        y = random.randrange(y - 75, y + 75)
        pos = x, y
        while self.scene.collide(get_box(pos, self.box)):
            x, y = [int(n) for n in self.coordinates.position]
            x = random.randrange(x - 75, x + 75)
            y = random.randrange(y - 75, y + 75)
            pos = x, y
        return pos

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
    def switch(self):
        return self.coordinates.y

    @property
    def image(self):
        return self.spritesheet.image(self.direction)

    def offset(self):
        inclination = self.scene.inclination_at(self.coordinates.position)
        position = self.coordinates.shift(self.direction, self.speed, inclination)
        box = get_box(position, self.box)
        if not self.scene.collide(box):
            self.coordinates.x = position[0]
            self.coordinates.y = position[1]
            return
        if self.direction not in DIRECTIONS.DIAGONALS:
            if self.status == CHARACTER_STATUSES.AUTOPILOT:
                self.end_autopilot()
            return
        box = get_box((self.coordinates.x, position[1]), self.box)
        if not self.scene.collide(box):
            self.coordinates.y = position[1]
            return
        box = get_box((position[0], self.coordinates.y), self.box)
        if not self.scene.collide(box):
            self.coordinates.x = position[0]

    def vomit(self):
        self.stop()
        self.spritesheet.animation = 'vomit'
        self.spritesheet.index = 0
        self.vomit_count_down = random.randrange(
            COUNTDOWNS.VOMIT_MIN, COUNTDOWNS.VOMIT_MAX)
        self.status = CHARACTER_STATUSES.STUCK

    def __next__(self):
        if self.vomit_count_down <= 0:
            self.vomit()
            return

        match self.status:
            case CHARACTER_STATUSES.AUTOPILOT:
                self.vomit_count_down -= 1
                return self.autopilot()

            case CHARACTER_STATUSES.OUT:
                conditions = (
                    self.spritesheet.animation_is_done and
                    self.buffer_animation)
                if conditions:
                    self.spritesheet.animation = self.buffer_animation
                    self.buffer_animation = None
                    next(self.spritesheet)
                    return
                conditions = (
                    self.spritesheet.animation_is_done and
                    self.spritesheet.animation in HOLDABLE_ANIMATIONS)
                if conditions:
                    return
                next(self.spritesheet)
                return

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
                    else:
                        self.status = CHARACTER_STATUSES.FREE
                        self.spritesheet.animation = 'idle'
                    self.spritesheet.index = 0
                    return
                next(self.spritesheet)
                return

        self.vomit_count_down -= 1

        if self.speed:
            self.offset()

        self.eval_animation()

    def eval_animation(self):
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
        for origin, _ in self.scene.possible_duels:
            if origin != self:
                continue

        self.status = CHARACTER_STATUSES.INTERACTING
        self.spritesheet.animation = 'call'
        self.spritesheet.index = 0

    def request_interaction(self):
        for zone in self.scene.interaction_zones:
            if zone.contains(self.coordinates.position):
                self.go_to(zone.target, zone.action, zone.direction)

    def go_to(self, position, action=None, direction=None):
        self.status = CHARACTER_STATUSES.AUTOPILOT
        self.ghost = None
        self.path = shortest_path(
            self.coordinates.position, position.copy())

        self.buffer_animation = action
        self.buffer_direction = direction

    def end_autopilot(self):
        self.stop()
        self.ghost = None
        if self.buffer_direction:
            self.direction = self.buffer_direction
        if self.buffer_animation:
            self.spritesheet.animation = self.buffer_animation
            self.spritesheet.index = 0
            self.buffer_animation = None
            self.status = CHARACTER_STATUSES.INTERACTING
        else:
            self.status = CHARACTER_STATUSES.FREE
        self.eval_animation()
        return

    def autopilot(self):

        if not self.path:
            self.end_autopilot()
            return

        current = self.coordinates.position
        direction = points_to_direction(current, self.path[0])
        self.direction = direction or self.direction
        self.accelerate()
        self.offset()
        if not self.ghost:
            if self.speed == 0:
                self.path.pop(0)
            self.ghost = self.coordinates.position
            self.eval_animation()
            return

        dist1 = distance(self.ghost, self.path[0])
        dist2 = distance(self.coordinates.position, self.path[0])
        if dist1 < dist2:
            self.coordinates.position = self.path.pop(0)[:]
            self.ghost = self.coordinates.position
            self.eval_animation()
            return
        self.ghost = self.coordinates.position
        self.eval_animation()


def points_to_direction(p1, p2):
    x = round(p1[0] - p2[0], 1)
    x = -1 if x > 0 else 1 if x < 0 else 0
    y = round(p1[1] - p2[1], 1)
    y = -1 if y > 0 else 1 if y < 0 else 0
    return HAT_TO_DIRECTION.get((x, y))


def equilateral_path(origin, dst):
    dst = list(dst)[:]
    dst[0] = dst[0] if dst[0] is not None else origin[0]
    dst[1] = dst[1] if dst[1] is not None else origin[1]
    if origin[0] in dst or origin[1] in dst:
        return [dst]
    intermediate = random.choice((
        [origin[0], dst[1]],
        [dst[0], origin[1]]))
    return [intermediate, dst]


def shortest_path(orig, dst):
    """
    Create a path between an origin and a destination lock to height
    directions. Function can contains some random to decide the way to use.
            ORIG------------- OTHER WAY POSSIBLE
                \            \
                 \------------ DST
            INTERMEDIATE
    """
    dst = list(dst)[:]
    dst[0] = dst[0] if dst[0] is not None else orig[0]
    dst[1] = dst[1] if dst[1] is not None else orig[1]

    if orig[0] in dst or orig[1] in dst:
        return [dst]

    reverse = random.choice([True, False])
    if reverse:
        orig, dst = dst, orig

    equi1 = dst[0], orig[1]
    equi2 = orig[0], dst[1]
    dist1 = distance(orig, equi1)
    dist2 = distance(orig, equi2)
    if dist1 > dist2:
        if dst[0] > orig[0]:
            intermediate = (equi2[0] + dist2, equi2[1])
        else:
            intermediate = (equi2[0] - dist2, equi2[1])
    else:
        if dst[1] > orig[1]:
            intermediate = (equi1[0], equi1[1] + dist1)
        else:
            intermediate = (equi1[0], equi1[1] - dist1)
    if reverse:
        orig, dst = dst, orig
    return [intermediate, dst]


