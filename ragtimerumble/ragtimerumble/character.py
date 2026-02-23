
import random
from ragtimerumble.config import (
    DIRECTIONS, SPEED, COUNTDOWNS, HOLDABLE_ANIMATIONS)
from ragtimerumble.config import LOOPING_ANIMATIONS, CHARACTER_STATUSES
from ragtimerumble.coordinates import Coordinates, get_box, box_hit_box
from ragtimerumble.io import play_sound
from ragtimerumble.pathfinding import shortest_path
from ragtimerumble.pilot import HardPathPilot


class Character:

    def __init__(self, position, spritesheet, palette, display_name, scene):
        self.spritesheet = spritesheet
        self.coordinates = Coordinates(position)
        self.direction = DIRECTIONS.DOWN
        self.palette = palette
        self.display_name = display_name
        self.speed = 0
        self.scene = scene
        self.vomit_count_down = random.randrange(
            COUNTDOWNS.VOMIT_MIN, COUNTDOWNS.VOMIT_MAX)
        self.status = CHARACTER_STATUSES.FREE
        self.duel_target = None
        self.pilot = None
        self.buffer_interaction_zone = None
        self.buffer_animation = None
        self.interacting_zone = None
        self.shorn = False

    @property
    def box(self):
        return self.spritesheet.data['box'][:]

    @property
    def hitbox(self):
        box = list(self.spritesheet.data['hitbox'])
        return get_box(self.coordinates.position, box)

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
        return self.spritesheet.image(self.direction, self.palette)

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
        play_sound('resources/sounds/vomit.wav')
        self.spritesheet.animation = 'vomit'

        self.spritesheet.index = 0
        self.vomit_count_down = random.randrange(
            COUNTDOWNS.VOMIT_MIN, COUNTDOWNS.VOMIT_MAX)
        self.status = CHARACTER_STATUSES.STUCK

    def evaluate_out(self):
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

    def evaluate_stuck(self):
        if self.spritesheet.animation_is_done:
            if self.spritesheet.animation == 'vomit':
                pos = self.render_position
                flipped = self.direction in DIRECTIONS.FLIPPED
                self.scene.create_vfx('vomit', pos, flipped)
            pos = self.coordinates.position
            if self.pilot and self.scene.inclination_at(pos):
                self.status = CHARACTER_STATUSES.AUTOPILOT
            else:
                self.status = CHARACTER_STATUSES.FREE
            self.stop()
        next(self.spritesheet)
        return

    def evaluate_interacting(self):
        if self.spritesheet.animation_is_done:
            match self.spritesheet.animation:
                case 'call':
                    self.spritesheet.animation = 'smoke'
                case 'death':
                    self.spritesheet.animation = 'coma'
                    self.status = CHARACTER_STATUSES.OUT
                case _:
                    if self.spritesheet.animation not in LOOPING_ANIMATIONS:
                        self.set_free()
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def __next__(self):
        if self.vomit_count_down <= 0:
            self.vomit()
            return

        match self.status:
            case CHARACTER_STATUSES.AUTOPILOT:
                self.vomit_count_down -= 1
                return self.autopilot()

            case CHARACTER_STATUSES.OUT:
                return self.evaluate_out()

            case CHARACTER_STATUSES.STUCK:
                return self.evaluate_stuck()

            case CHARACTER_STATUSES.INTERACTING:
                return self.evaluate_interacting()

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
        inclination = self.scene.inclination_at(self.coordinates.position)
        if self.pilot and inclination:
            self.status = CHARACTER_STATUSES.AUTOPILOT
        else:
            self.status = CHARACTER_STATUSES.FREE
        self.spritesheet.animation = 'idle'
        self.spritesheet.index = 0
        if self.interacting_zone:
            if self.interacting_zone.play_once:
                self.interacting_zone.enable = False
            if self.interacting_zone.out_sound:
                play_sound(self.interacting_zone.out_sound)
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

    def kill(self, target, black_screen=False, silently=False):
        black_screen = black_screen and self.scene.apply_black_screen(
            self, target)
        self.stop()
        play_sound('resources/sounds/colt.wav')
        target.stop()
        if black_screen:
            self.status = CHARACTER_STATUSES.FREE
            self.spritesheet.animation = 'idle'
            target.aim(self)
        elif not silently:
            self.status = CHARACTER_STATUSES.INTERACTING
            self.spritesheet.animation = 'gunshot'
            target.aim(self)
        self.spritesheet.index = 0
        target.status = CHARACTER_STATUSES.OUT
        target.spritesheet.animation = 'death'
        target.spritesheet.index = 0
        if self.duel_target and self.duel_target is target:
            if not black_screen and silently:  # from sniper
                self.status = CHARACTER_STATUSES.FREE
                self.spritesheet.animation = 'idle'
            self.duel_target.duel_target = None
            self.duel_target = None
        if self.interacting_zone:
            self.interacting_zone.busy = False
            self.interacting_zone = None
        self.scene.kill_message(self, target)

    def release_duel(self):
        target = self.duel_target
        if target:
            target.spritesheet.animation = 'idle'
            target.spritesheet.index = 0
            status = (
                CHARACTER_STATUSES.AUTOPILOT if target.pilot
                else CHARACTER_STATUSES.FREE)
            target.status = status
            target.duel_target = None
            target = None
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
            position = self.coordinates.position
            inclination = self.scene.inclination_at(position)
            if not inclination:
                self.pilot = None
            target.stop()
            target.status = CHARACTER_STATUSES.DUEL_TARGET
            target.spritesheet.animation = 'suspicious'
            target.spritesheet.index = 0
            target.aim(self)
            target.duel_target = self
            position = target.coordinates.position
            inclination = self.scene.inclination_at(position)
            if not inclination:
                target.pilot = None
            target.hardpath = None
            play_sound('resources/sounds/woosh.wav')
            return

    def request_interaction(self):
        zones = [z for z in self.scene.interaction_zones if z.enable]
        zones += self.scene.interactive_props
        for zone in zones:
            if zone.contains(self.coordinates.position) and not zone.busy:
                self.go_to(zone.target, zone)
                return True

    def request_stripping(self):
        solvent = [
            character for character in self.scene.characters if
            character.status == CHARACTER_STATUSES.OUT and
            character.shorn is False]
        for character in solvent:
            if box_hit_box(character.screen_box, self.screen_box):
                return character

    def attraction_zone(self):
        zones = self.scene.interactive_props + self.scene.interaction_zones
        return next((
            zone for zone in zones if
            zone.attract(self.coordinates.position)), None)

    def shadow_zone(self):
        box = get_box(self.coordinates.position, self.box)
        return self.scene.instersected_shadow_zone(box)

    def go_to(self, position, zone=None):
        self.status = CHARACTER_STATUSES.AUTOPILOT
        path = shortest_path(self.coordinates.position, position.copy())
        self.pilot = HardPathPilot(self, path)
        self.buffer_interaction_zone = zone

    def end_autopilot(self):
        self.stop()
        self.pilot = None
        zone = self.buffer_interaction_zone
        if not zone or zone.busy:
            self.status = CHARACTER_STATUSES.FREE
            self.buffer_interaction_zone = None
            return
        if zone.in_sound:
            play_sound(zone.in_sound)
        self.spritesheet.animation = zone.action
        self.spritesheet.index = 0
        self.direction = zone.direction
        self.interacting_zone = zone
        self.interacting_zone.busy = zone.lockable
        self.status = CHARACTER_STATUSES.INTERACTING
        self.buffer_interaction_zone = None
        if zone.destroyable:
            self.scene.destroy(zone.id)

    def autopilot(self):
        try:
            next(self.pilot)
        except StopIteration:
            self.end_autopilot()
        self.eval_animation()
