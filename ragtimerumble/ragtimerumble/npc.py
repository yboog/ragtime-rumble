import sys
import random
import itertools

from ragtimerumble.config import (
    COUNTDOWNS, SMOOTH_PATH_SELECTION_RADIUS, SMOOTH_PATH_USAGE_PROBABILITY,
    HARD_PATH_SELECTION_RADIUS, DIRECTIONS, DOG_GROWL_DISTANCE,
    DOG_BARK_DISTANCE)
from ragtimerumble.config import (
    CHARACTER_STATUSES, SPEED, HARD_PATH_USAGE_PROBABILITY)
from ragtimerumble.coordinates import Coordinates, path_cross_rect
from ragtimerumble.io import (
    choice_death_sentence, choice_random_name, load_data, image_mirror,
    play_sound)
from ragtimerumble.pathfinding import (
    point_in_rectangle, shortest_path, smooth_path_to_path, equilateral_path,
    filter_close_paths, points_to_direction, distance, choice_destination)
from ragtimerumble.pilot import SmoothPathPilot, HardPathPilot
from ragtimerumble.sprite import SpriteSheet
from ragtimerumble.sniperreticle import SniperReticle


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

    def release_target(self):
        target = self.character.duel_target
        target.duel_target = None
        target.spritesheet.animation = 'idle'
        target.spritesheet.index = 0
        target.status = (
            CHARACTER_STATUSES.AUTOPILOT if target.pilot else
            CHARACTER_STATUSES.FREE)
        self.character.duel_target = None

    def fall_to_coma(self):
        if self.character.status == CHARACTER_STATUSES.OUT:
            next(self.character)
            return

        if self.character.duel_target:
            self.release_target()

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
                self.character.pilot = None
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
            path = self.look_for_hard_path()
            if path:
                pilot = HardPathPilot(self.character, path)
            else:
                pilot = SmoothPathPilot(self.character, self.build_path())
            self.character.pilot = pilot
            self.character.status = CHARACTER_STATUSES.AUTOPILOT
            next(self.character)
            return

        if self.character.speed:
            self.character.decelerate()
        self.cool_down -= 1
        next(self.character)

    def look_for_hard_path(self):
        if not random.choice(range(HARD_PATH_USAGE_PROBABILITY)):
            return None
        position = self.character.coordinates.position
        paths = filter_close_paths(
            position, self.scene.hard_paths,
            HARD_PATH_SELECTION_RADIUS)
        if not paths:
            return
        path = random.choice(paths)
        pre_path = shortest_path(self.character.coordinates.position, path[0])
        return pre_path + path

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
        box = self.character.box
        destination = choice_destination(self.scene, position, box)
        path = func(position, destination)
        for stair in self.scene.stairs:  # Avoid smooth path in stairs.
            if path_cross_rect(path, stair['zone']):
                return self.build_path()
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


class Sniper:
    def __init__(
            self, scene=None, file=None,
            startposition=None, zone=None,
            interaction_zone=None, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'idle')
        self.coordinates = Coordinates((startposition))
        self.reticle = SniperReticle(zone, scene)
        self.interaction_zone = interaction_zone
        self.scene = scene
        self.price = 1
        self.zone = zone
        scene.sniperreticles.append(self.reticle)

    def create_coin_vfx(self):
        position = list(self.coordinates.position)
        position[0] += 25
        self.scene.create_vfx('coin-alert', position)

    def corruption_attempt(self, player):
        if self.spritesheet.animation == 'gunshot-goback':
            return False
        if self.price > player.coins:
            return False
        if player == self.reticle.player:
            return False
        player.coins -= self.price
        self.price += 1
        if self.spritesheet.animation == 'idle':
            self.spritesheet.animation = 'go-aim'
            self.spritesheet.index = 0
        self.reticle.player = player
        self.create_coin_vfx()
        return True

    def meet(self, position):
        return point_in_rectangle(position, *self.interaction_zone)

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return 2000

    def __next__(self):
        next(self.reticle)
        if not self.spritesheet.animation_is_done:
            next(self.spritesheet)
            return

        match self.spritesheet.animation:
            case 'idle':
                self.spritesheet.index = 0
            case 'aim-idle':
                self.spritesheet.index = 0
            case 'go-aim':
                self.spritesheet.animation = 'aim-idle'
                self.spritesheet.index = 0
            case 'gunshot-goback':
                self.spritesheet.animation = 'idle'
                self.spritesheet.index = 0

    def shoot(self):
        self.price = 1
        self.reticle.shoot()
        self.spritesheet.animation = 'gunshot-goback'
        self.spritesheet.index = 0

    @property
    def image(self):
        return self.spritesheet.image()


class Pianist:
    slows = [
        'slow1',
        'slow2',
        'slow3',
        'slow4']
    fasts = [
        'fast1',
        'fast2',
        'fast3',
        'fast4']

    def __init__(self, file='', startposition=None, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'slow1')
        self.coordinates = Coordinates((startposition))
        self.sequence = []

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return self.data['y']

    def next_animation(self):
        if not self.sequence:
            slow = random.choice((False, True))
            if slow:
                return random.choice(self.slows)
            self.sequence = [
                random.choice(self.fasts),
                random.choice(self.fasts)]
        return self.sequence.pop()

    def __next__(self):
        if self.spritesheet.animation_is_done:
            self.spritesheet.animation = self.next_animation()
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    @property
    def image(self):
        return self.spritesheet.image()


class Dog:
    def __init__(
            self, scene=None, file=None, startposition=None,
            path=None, direction=None, **_):
        self.data = load_data(file)
        self.scene = scene
        self.spritesheet = SpriteSheet(self.data, 'sit')
        self.coordinates = Coordinates((startposition))
        self.behavior_cooldown = random.randint(
            *COUNTDOWNS.DOG_IDLE_COOLDOWN_RANGE)
        self.path = itertools.cycle(path)
        self.destination = next(self.path)
        self.direction = direction

    def closest_player_distance(self):
        distance = sys.maxsize
        for player in self.scene.players:
            if player.dying or player.dead:
                continue
            if player.character.status == CHARACTER_STATUSES.INTERACTING:
                continue
            coordinates = player.character.coordinates
            distance = min((
                distance,
                self.coordinates.distance_to(coordinates)))
        return distance

    @property
    def render_position(self):
        offset_x, offset_y = self.spritesheet.data['center']
        return self.coordinates.x - offset_x, self.coordinates.y - offset_y

    @property
    def switch(self):
        return self.coordinates.y

    @property
    def image(self):
        if self.direction not in DIRECTIONS.FLIPPED:
            return image_mirror(self.spritesheet.image(), horizontal=True)
        return self.spritesheet.image()

    def walk(self):
        self.behavior_cooldown -= 1
        p1 = self.coordinates.position
        direction = points_to_direction(p1, self.destination)
        if not direction:
            self.destination = next(self.path)
            return self.walk()
        self.direction = direction
        p2 = self.coordinates.shift(direction, SPEED.DOG, 0)
        if distance(p1, self.destination) < distance(p2, self.destination):
            self.destination = next(self.path)
            return self.walk()

        self.coordinates.position = p2
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def __next__(self):

        animation = self.spritesheet.animation
        if animation == 'bark' and not self.spritesheet.animation_is_done:
            next(self.spritesheet)
            return

        distance = self.closest_player_distance()
        if 0 < distance < DOG_BARK_DISTANCE:
            if animation == 'bark' and not self.spritesheet.animation_is_done:
                next(self.spritesheet)
                return
            play_sound('resources/sounds/barkling.wav')
            self.spritesheet.animation = 'bark'
            self.spritesheet.index = 0
            return
        elif DOG_BARK_DISTANCE < distance < DOG_GROWL_DISTANCE:
            if animation in ('bark', 'growl'):
                if not self.spritesheet.animation_is_done:
                    next(self.spritesheet)
                    return
            play_sound('resources/sounds/growling.wav')
            self.spritesheet.animation = 'growl'
            self.spritesheet.index = 0
            return

        if self.behavior_cooldown > 0 and animation == 'siderun':
            self.walk()
            return

        idles = 'sit', 'idle'
        if self.behavior_cooldown > 0 and animation in idles:
            self.behavior_cooldown -= 1
            if self.spritesheet.animation_is_done:
                self.spritesheet.index = 0
                return
            next(self.spritesheet)
            return

        if self.behavior_cooldown == 0 and animation == 'siderun':
            self.behavior_cooldown = random.randint(
                *COUNTDOWNS.DOG_IDLE_COOLDOWN_RANGE)
            self.spritesheet.animation = random.choice(idles)
            self.spritesheet.index = 0
            next(self.spritesheet)
            return

        if self.behavior_cooldown == 0 and animation in idles:
            self.behavior_cooldown = random.randint(
                *COUNTDOWNS.DOG_WALK_COOLDOWN_RANGE)
            self.spritesheet.animation = 'siderun'
            self.spritesheet.index = 0
            next(self.spritesheet)
            return

        if animation in ('bark', 'growl'):
            if not self.spritesheet.animation_is_done:
                next(self.spritesheet)
                return
            self.spritesheet.animation = random.choice(('sit', 'idle'))
            self.spritesheet.index = 0

        next(self.spritesheet)


class Barman:

    def __init__(self, file=None, startposition=None, path=None, **_):
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
