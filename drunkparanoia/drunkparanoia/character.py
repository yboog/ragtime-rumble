
import random
from drunkparanoia.config import (
    DIRECTIONS, SPEED, COUNTDOWNS, HOLDABLE_ANIMATIONS)
from drunkparanoia.config import LOOPING_ANIMATIONS, CHARACTER_STATUSES
from drunkparanoia.coordinates import Coordinates, get_box, distance
from drunkparanoia.pathfinding import shortest_path, points_to_direction


class Character:
    def __init__(self, position, spritesheet, variation, scene):
        self.spritesheet = spritesheet
        self.coordinates = Coordinates(position)
        self.direction = DIRECTIONS.DOWN
        self.variation = variation
        self.gender = 'man'
        self.speed = 0
        self.scene = scene
        self.vomit_count_down = random.randrange(
            COUNTDOWNS.VOMIT_MIN, COUNTDOWNS.VOMIT_MAX)
        self.status = CHARACTER_STATUSES.FREE
        self.duel_target = None
        self.ghost = None
        self.path = None
        self.buffer_interaction_zone = None
        self.buffer_animation = None
        self.interacting_zone = None

    def choice_destination(self):
        limit = 0
        while True:
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
        return self.spritesheet.image(self.direction, self.variation)

    def offset(self):
        inclination = self.scene.inclination_at(self.coordinates.position)
        position = self.coordinates.shift(
            self.direction, self.speed, inclination)
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
                    self.spritesheet.index = 0
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
                    if self.spritesheet.animation == 'vomit':
                        pos = self.render_position
                        flipped = self.direction in DIRECTIONS.FLIPPED
                        self.scene.create_vfx('vomit', pos, flipped)
                    self.status = CHARACTER_STATUSES.FREE
                    self.stop()
                next(self.spritesheet)
                return

            case CHARACTER_STATUSES.INTERACTING:
                if self.spritesheet.animation_is_done:
                    match self.spritesheet.animation:
                        case 'call':
                            self.spritesheet.animation = 'smoke'
                        case 'death':
                            self.spritesheet.animation = 'coma'
                            self.status = CHARACTER_STATUSES.OUT
                        case _:
                            looping = LOOPING_ANIMATIONS
                            if self.spritesheet.animation not in looping:
                                self.set_free()
                    self.spritesheet.index = 0
                    return
                next(self.spritesheet)
                return

            case CHARACTER_STATUSES.DUEL_ORIGIN:
                if self.spritesheet.animation_is_done:
                    return
                next(self.spritesheet)
                return

            case CHARACTER_STATUSES.DUEL_TARGET:
                if self.spritesheet.animation_is_done:
                    return
                next(self.spritesheet)
                return

        self.vomit_count_down -= 1

        if self.speed:
            self.offset()

        self.eval_animation()

    def set_free(self):
        self.status = CHARACTER_STATUSES.FREE
        self.spritesheet.animation = 'idle'
        self.spritesheet.index = 0
        if self.interacting_zone:
            self.interacting_zone.busy = False
            self.interacting_zone = None

    def aim(self, character):
        if self.coordinates.x > character.coordinates.x:
            self.direction = DIRECTIONS.LEFT
        else:
            self.direction = DIRECTIONS.RIGHT

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

    def kill(self, target, black_screen=False):
        black_screen = black_screen and self.scene.apply_black_screen(
            self, target)
        self.stop()
        if black_screen:
            self.status = CHARACTER_STATUSES.FREE
            self.spritesheet.animation = 'idle'
        else:
            self.status = CHARACTER_STATUSES.INTERACTING
            self.spritesheet.animation = 'gunshot'
        self.spritesheet.index = 0
        target.stop()
        target.aim(self)
        target.status = CHARACTER_STATUSES.OUT
        target.spritesheet.animation = 'death'
        target.spritesheet.index = 0
        if self.duel_target:
            self.duel_target.duel_target = None
            self.duel_target = None
        self.scene.kill_message(self, target)

    def release_duel(self):
        if self.duel_target:
            self.duel_target.spritesheet.animation = 'idle'
            self.duel_target.spritesheet.index = 0
            self.duel_target.status = CHARACTER_STATUSES.FREE
            self.duel_target.duel_target = None
            self.duel_target = None
        self.status = CHARACTER_STATUSES.INTERACTING
        self.spritesheet.animation = 'smoke'
        self.spritesheet.index = 0

    def request_duel(self):
        for origin, target in self.scene.possible_duels:
            if origin != self:
                continue
            self.stop()
            self.status = CHARACTER_STATUSES.DUEL_ORIGIN
            self.spritesheet.animation = 'call'
            self.spritesheet.index = 0
            self.duel_target = target
            self.path = None
            target.stop()
            target.status = CHARACTER_STATUSES.DUEL_TARGET
            target.spritesheet.animation = 'suspicious'
            target.spritesheet.index = 0
            target.aim(self)
            target.duel_target = self
            target.path = None
            return

    def request_interaction(self):
        for zone in self.scene.interaction_zones:
            if zone.contains(self.coordinates.position) and not zone.busy:
                self.go_to(zone.target, zone)
                return True
        return False

    def attraction_zone(self):
        return next((
            zone for zone in self.scene.interaction_zones if
            zone.attract(self.coordinates.position)), None)

    def go_to(self, position, zone=None):
        self.status = CHARACTER_STATUSES.AUTOPILOT
        self.ghost = None
        self.path = shortest_path(self.coordinates.position, position.copy())
        self.buffer_interaction_zone = zone

    def end_autopilot(self):
        self.stop()
        self.ghost = None
        zone = self.buffer_interaction_zone
        if zone and not zone.busy:
            self.spritesheet.animation = zone.action
            self.spritesheet.index = 0
            self.direction = zone.direction
            self.interacting_zone = zone
            self.interacting_zone.busy = True
            self.status = CHARACTER_STATUSES.INTERACTING
        else:
            self.status = CHARACTER_STATUSES.FREE
        self.buffer_interaction_zone = None
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
        elif self.ghost == self.coordinates.position:
            self.end_autopilot()
            self.path = None
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
