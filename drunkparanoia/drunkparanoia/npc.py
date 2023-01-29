
import random
import itertools
from drunkparanoia.config import (
    COUNTDOWNS, SMOOTH_PATH_SELECTION_RADIUS, SMOOTH_PATH_USAGE_PROBABILITY)
from drunkparanoia.io import choice_death_sentence, choice_random_name, load_data
from drunkparanoia.config import CHARACTER_STATUSES, DIRECTIONS, SPEED
from drunkparanoia.coordinates import Coordinates
from drunkparanoia.pathfinding import (
    shortest_path, smooth_path_to_path, equilateral_path, filter_close_paths,
    points_to_direction, distance)
from drunkparanoia.sprite import SpriteSheet


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
                if player else choice_random_name(self.character.gender))
            messenger = self.scene.messenger
            sentence = choice_death_sentence('french')
            messenger.add_message(sentence.format(name=name))
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


class Pianist:
    def __init__(self, file, startposition, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'slow1')
        self.coordinates = Coordinates((startposition))

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return self.data['y']

    def __next__(self):
        if self.spritesheet.animation_is_done:
            animation = random.choice(list(self.data['animations']))
            self.spritesheet.animation = animation
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    @property
    def image(self):
        return self.spritesheet.image()


class Barman():

    def __init__(self, file, startposition, path, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'idle')
        self.coordinates = Coordinates((startposition))
        self.idle_cooldown = random.randint(
            *COUNTDOWNS.BARMAN_IDLE_COOLDOWN_RANGE)
        self.walk_cooldown = 0
        self.path = itertools.cycle(path)
        self.destination = next(self.path)

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return self.data['y']

    @property
    def image(self):
        return self.spritesheet.image()

    def walk(self):
        self.walk_cooldown -= 1
        p1 = self.coordinates.position
        direction = points_to_direction(p1, self.destination)
        if not direction:
            self.destination = next(self.path)
            return self.walk()
        p2 = self.coordinates.shift(direction, SPEED.BARMAN, 0)
        if distance(p1, self.destination) < distance(p2, self.destination):
            self.destination = next(self.path)
            return self.walk()

        self.coordinates.position = p2
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def __next__(self):

        if self.walk_cooldown > 0 and self.spritesheet.animation == 'walk':
            self.walk()
            return

        idles = 'towel', 'idle'
        anim = self.spritesheet.animation
        if anim in idles and self.idle_cooldown > 0:
            self.idle_cooldown -= 1
            if self.spritesheet.animation_is_done:
                self.spritesheet.index = 0
            next(self.spritesheet)
            return

        if anim == 'towel':
            self.spritesheet.animation = 'towel-end'
            self.spritesheet.index = 0
            return

        if anim == 'towel-end' and not self.spritesheet.animation_is_done:
            next(self.spritesheet)
            return

        if anim == 'towel-start':
            if not self.spritesheet.animation_is_done:
                next(self.spritesheet)
                return
            self.idle_cooldown = random.randint(
                *COUNTDOWNS.BARMAN_IDLE_COOLDOWN_RANGE)
            self.spritesheet.animation = 'towel'
            self.spritesheet.index = 0
            return

        # Set new behavior
        match random.choice(('towel', 'idle', 'walk')):
            case 'towel':
                self.spritesheet.animation = 'towel-start'
                self.spritesheet.index = 0
                return
            case 'idle':
                self.idle_cooldown = random.randint(
                    *COUNTDOWNS.BARMAN_IDLE_COOLDOWN_RANGE)
                self.spritesheet.animation = 'idle'
                self.spritesheet.index = 0
                return
            case 'walk':
                self.spritesheet.animation = 'walk'
                self.spritesheet.index = 0
                self.walk_cooldown = random.randint(
                    *COUNTDOWNS.BARMAN_WALK_COOLDOWN_RANGE)

        next(self.spritesheet)
