
import random
from drunkparanoia.config import (
    DIRECTIONS, SPEED, COUNTDOWNS, HAT_TO_DIRECTION, HOLDABLE_ANIMATIONS,
    SMOOTH_PATH_SELECTION_RADIUS, SMOOTH_PATH_USAGE_PROBABILITY)
from drunkparanoia.io import choice_death_sentence, choice_random_name
from drunkparanoia.joystick import get_pressed_direction, get_current_commands
from drunkparanoia.config import LOOPING_ANIMATIONS, CHARACTER_STATUSES
from drunkparanoia.coordinates import Coordinates, get_box, distance


class Player:

    def __init__(self, character, joystick, index, scene):
        self.character = character
        self.scene = scene
        self.joystick = joystick
        self.life = COUNTDOWNS.MAX_LIFE
        self.bullet_cooldown = 0
        self.action_cooldown = 0
        self.index = index
        self.killer = None
        self.npc_killed = 0

    @property
    def dying(self):
        return (
            self.life == 0 and self.character.status != CHARACTER_STATUSES.OUT)

    @property
    def dead(self):
        return self.character.status == CHARACTER_STATUSES.OUT

    def kill(self, target, black_screen=False):
        self.character.kill(target, black_screen)
        player = self.scene.find_player(target)
        if player:
            player.killer = self.index
            player.life = 0
        else:
            self.npc_killed += 1
        self.bullet_cooldown = COUNTDOWNS.BULLET_COOLDOWN

    def __next__(self):
        # self.life -= 1
        if self.character.status == CHARACTER_STATUSES.OUT:
            next(self.character)
            return

        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

        if self.action_cooldown > 0:
            self.action_cooldown -= 1

        match self.character.status:
            case CHARACTER_STATUSES.STUCK:
                next(self.character)
                return

            case CHARACTER_STATUSES.FREE:
                if self.evaluate_free():
                    return

            case CHARACTER_STATUSES.DUEL_ORIGIN:
                return self.evaluate_duel_as_origin()

            case CHARACTER_STATUSES.DUEL_TARGET:
                return self.evaluate_duel_as_target()

            case CHARACTER_STATUSES.INTERACTING:
                return self.evaluate_interacting()

            case CHARACTER_STATUSES.AUTOPILOT:
                next(self.character)
                return

        direction = get_pressed_direction(self.joystick)
        if direction:
            self.character.direction = direction
            self.character.accelerate()
        else:
            self.character.decelerate()
        next(self.character)

    def evaluate_interacting(self):
        is_looping = self.character.spritesheet.animation in LOOPING_ANIMATIONS
        commands = get_current_commands(self.joystick)
        if not is_looping or not commands.get('X') or self.action_cooldown:
            next(self.character)
            return
        self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN
        self.character.set_free()

    def evaluate_duel_as_target(self):
        commands = get_current_commands(self.joystick)
        if commands.get('X') and not self.bullet_cooldown:
            target = self.character.duel_target
            self.character.aim(target)
            self.kill(target, black_screen=True)
        if not self.character.spritesheet.animation_is_done:
            next(self.character)

    def evaluate_duel_as_origin(self):
        if not self.character.spritesheet.animation_is_done:
            next(self.character)
            return
        commands = get_current_commands(self.joystick)
        if commands.get('X') and not self.bullet_cooldown:
            self.kill(self.character.duel_target, black_screen=True)

        if commands.get('A'):
            self.character.release_duel()
        next(self.character)

    def evaluate_free(self):
        commands = get_current_commands(self.joystick)
        if commands.get('A'):
            self.character.stop()
            self.character.request_duel()
            return True
        if commands.get('X'):
            if not self.bullet_cooldown:
                for character1, character2 in self.scene.possible_duels:
                    if character1 == self.character:
                        self.kill(character2)
                        self.scene.apply_white_screen(self.character)
                        return True
            if self.action_cooldown != 0:
                return
            interact = self.character.request_interaction()
            if interact:
                self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN


class Npc:

    def __init__(self, character, scene):
        self.character = character
        self.scene = scene
        self.next_duel_check_countdown = random.randrange(
            COUNTDOWNS.DUEL_CHECK_MIN, COUNTDOWNS.DUEL_CHECK_MAX)
        self.coma_count_down = random.randrange(
            COUNTDOWNS.COMA_MIN, COUNTDOWNS.COMA_MAX)
        self.interaction_cooldown = random.randrange(
            COUNTDOWNS.INTERACTION_COOLDOWN_MIN,
            COUNTDOWNS.INTERACTION_COOLDOWN_MAX)
        self.interaction_loop_cooldown = 0
        self.cool_down = 0
        self.release_time = 0
        self.is_cooling_down = False

    def test_duels(self):
        if self.next_duel_check_countdown > 0:
            self.next_duel_check_countdown -= 1
            return False
        origin = [c for c, _ in self.character.scene.possible_duels]
        if self.character not in origin:
            return False
        self.character.request_duel()
        self.next_duel_check_countdown = random.randrange(
            COUNTDOWNS.DUEL_CHECK_MIN, COUNTDOWNS.DUEL_CHECK_MAX)
        self.release_time = random.randrange(
            COUNTDOWNS.DUEL_RELEASE_TIME_MIN,
            COUNTDOWNS.DUEL_RELEASE_TIME_MAX)
        return True

    def fall_to_coma(self):
        if self.character.status != CHARACTER_STATUSES.OUT:
            if self.character.duel_target:
                self.character.duel_target.duel_target = None
                self.character.duel_target.spritesheet.animation = 'idle'
                self.character.duel_target.spritesheet.index = 0
                self.character.duel_target.status = CHARACTER_STATUSES.FREE
                self.character.duel_target = None

            self.character.status = CHARACTER_STATUSES.OUT
            self.character.spritesheet.animation = 'vomit'
            self.character.spritesheet.index = 0
            self.character.buffer_animation = 'coma'
            player = self.scene.find_player(self)
            name = (
                f'Player {player.index + 1}'
                if player else choice_random_name('man'))
            messenger = self.scene.messenger
            messenger.add_message(choice_death_sentence('french').format(name=name))
            return
        next(self.character)

    def interaction_zone(self):
        condition = (
            (zone := self.character.attraction_zone()) and
            self.interaction_cooldown == 0 and
            random.choice(range(COUNTDOWNS.INTERACTION_PROBABILITY)) == 0)
        if condition:
            return zone

    def evaluate_free(self):
        if self.test_duels():
            return

        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1

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

        if zone := self.interaction_zone():
            self.character.go_to(zone.target, zone)
            self.interaction_cooldown = random.randrange(
                COUNTDOWNS.INTERACTION_COOLDOWN_MIN,
                COUNTDOWNS.INTERACTION_COOLDOWN_MAX)
            next(self.character)
            return

        if self.cool_down == 0:
            self.character.end_autopilot()
            self.is_cooling_down = False
            self.character.status = CHARACTER_STATUSES.AUTOPILOT
            self.character.ghost = None
            self.character.path = self.build_path()
            self.character.autopilot()
            next(self.character)
            return

        if self.character.speed:
            self.character.decelerate()
        self.cool_down -= 1
        next(self.character)

    def build_path(self):
        position = self.character.coordinates.position
        if random.choice(range(SMOOTH_PATH_USAGE_PROBABILITY)) == 0:
            paths = filter_close_paths(
                position, self.scene.smooth_paths,
                SMOOTH_PATH_SELECTION_RADIUS)
            if paths:
                return smooth_path_to_path(position, random.choice(paths))

        functions = [shortest_path] * 2 + [equilateral_path]
        func = random.choice(functions)
        destination = self.character.choice_destination()
        return func(position, destination)

    def __next__(self):
        if self.coma_count_down == 0:
            return self.fall_to_coma()
        self.coma_count_down -= 1

        match self.character.status:
            case CHARACTER_STATUSES.INTERACTING:
                if self.interaction_loop_cooldown <= 0:
                    self.character.set_free()
                    self.interaction_loop_cooldown = random.choice(range(
                        COUNTDOWNS.INTERACTION_LOOP_COOLDOWN_MIN,
                        COUNTDOWNS.INTERACTION_LOOP_COOLDOWN_MAX))
                    return
                self.interaction_loop_cooldown -= 1
                next(self.character)
                return

            case CHARACTER_STATUSES.AUTOPILOT:
                if self.test_duels():
                    return
                next(self.character)
                return

            case CHARACTER_STATUSES.FREE:
                self.evaluate_free()

            case CHARACTER_STATUSES.DUEL_ORIGIN:
                if not self.character.spritesheet.animation_is_done:
                    next(self.character)
                    return
                if self.release_time == 0:
                    self.character.release_duel()
                    next(self.character)
                    return
                self.release_time -= 1
                return

        next(self.character)


class Character:
    def __init__(self, position, spritesheet, variation, scene):
        self.spritesheet = spritesheet
        self.coordinates = Coordinates(position)
        self.direction = DIRECTIONS.DOWN
        self.variation = variation
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
        black_screen = black_screen and self.scene.apply_black_screen(self, target)
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
        target.status = CHARACTER_STATUSES.INTERACTING
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


def filter_close_paths(point, paths, maxdistance):
    return [path for path in paths if distance(point, path[0]) < maxdistance]


def smooth_path_to_path(orig, points):
    path = []
    for point in points:
        path.extend(shortest_path(orig, point))
        orig = point
    return path


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
