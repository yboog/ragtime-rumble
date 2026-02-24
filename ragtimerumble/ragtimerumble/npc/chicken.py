import sys

from ragtimerumble.config import (
    COUNTDOWNS, CHICKEN_RUNDISTANCE, DIRECTIONS)
from ragtimerumble.config import CHARACTER_STATUSES, SPEED
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data, play_sound
from ragtimerumble.mathutils import set_vector_length
from ragtimerumble.pathfinding import (
    shortest_path, points_to_direction, distance, random_position_in_rect)
from ragtimerumble.randomutils import choose
from ragtimerumble.sprite import SpriteSheet


class Chicken:
    IDLE_ANIMATIONS = {
        'idle-a': 8,
        'idle-b': 5,
        'idle-c': 5,
        'idle-d': 5,
        'idle-e': 3,
        'idle-f': 10,
        'idle-g': 1,
        'idle-h': 1,
        'idle-i': 1,
        'scratch': 2}
    ANIMATION_SOUNDS = {
        'idle-h': '/resources/sounds/cluck-1.wav',
        'idle-e': '/resources/sounds/cluck-2.wav',
        'idle-g': '/resources/sounds/cluck-3.wav',
        'scratch': '/resources/sounds/chicken-scratch.wav',
    }

    def __init__(
            self, scene=None, file=None, startposition=None, zone=None, **_):
        self.data = load_data(file)
        self.scene = scene
        self.spritesheet = SpriteSheet(self.data, 'idle-a')
        self.startposition = startposition
        self.coordinates = Coordinates((startposition))
        self.path = None
        self.direction = DIRECTIONS.LEFT
        self.destination = None
        self.run_cooldown = 0
        self.zone = zone

    def closest_player_distance(self):
        min_distance = sys.maxsize
        closest_player = None
        for player in self.scene.players:
            if player.dying or player.dead:
                continue
            if player.character.status == CHARACTER_STATUSES.INTERACTING:
                continue
            coordinates = player.character.coordinates
            distance = self.coordinates.distance_to(coordinates)
            if distance < min_distance:
                min_distance = distance
                closest_player = player
        return min_distance, closest_player

    @property
    def render_position(self):
        offset_x, offset_y = self.spritesheet.data['center']
        return self.coordinates.x - offset_x, self.coordinates.y - offset_y

    @property
    def switch(self):
        return self.data['y'] + self.coordinates.y

    @property
    def image(self):
        return self.spritesheet.image(self.direction)

    def check_run(self):
        if self.run_cooldown > 0 or self.spritesheet.animation == 'runcycle':
            return False
        distance, player = self.closest_player_distance()
        if distance > CHICKEN_RUNDISTANCE or player is None:
            return False
        coordinates = player.character.coordinates
        x = coordinates.position[0] - self.coordinates.position[0]
        y = coordinates.position[1] - self.coordinates.position[1]
        v = set_vector_length([x, y], 50)
        dst = self.startposition[0] - v[0], self.startposition[1] - v[1]

        self.path = iter(shortest_path(self.coordinates.position, dst))
        self.spritesheet.animation = 'runcycle'
        self.destination = next(self.path)
        self.spritesheet.index = 1
        self.walk()
        play_sound('/resources/sounds/chicken-scream.wav')
        self.run_cooldown = COUNTDOWNS.CHICKEN_RUN_COOLDOWN
        return True

    def __next__(self):
        if self.check_run():
            return
        self.run_cooldown = max((0, self.run_cooldown - 1))
        next(self.spritesheet)

        if self.spritesheet.animation in self.IDLE_ANIMATIONS:
            if self.spritesheet.animation_is_done:
                continue_idle = choose({True: 4, False: 1})
                if continue_idle:
                    return self.set_idle()
                return self.start_walk()
        if self.spritesheet.animation in ('walkcycle', 'runcycle'):
            self.walk()

    def start_walk(self):
        dst = random_position_in_rect(self.zone)
        self.path = iter(shortest_path(self.coordinates.position, dst))
        self.spritesheet.animation = 'walkcycle'
        self.destination = next(self.path)
        self.spritesheet.index = 1
        self.walk()

    def walk(self):
        p1 = self.coordinates.position
        direction = points_to_direction(p1, self.destination)
        if not direction:
            self.destination = next(self.path)
            return self.walk()
        speed = (
            SPEED.CHICKEN_WALK if self.spritesheet.animation == 'walkcycle'
            else SPEED.CHICKEN_RUN)
        p2 = self.coordinates.shift(direction, speed, 0)
        if p2[0] > p1[0]:
            self.direction = DIRECTIONS.LEFT
        else:
            self.direction = DIRECTIONS.RIGHT

        if distance(p1, self.destination) < distance(p2, self.destination):
            try:
                self.destination = next(self.path)
                return self.walk()
            except StopIteration:
                self.set_idle()

        self.coordinates.position = p2
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        next(self.spritesheet)

    def set_idle(self):
        # Avoid looping the same animation
        possible_animations = {
            k: v for k, v in self.IDLE_ANIMATIONS.items()
            if k != self.spritesheet.animation}
        animation = choose(possible_animations)
        sound = self.ANIMATION_SOUNDS.get(animation)
        # if sound:
        #     play_sound(sound)
        self.spritesheet.animation = animation
        self.spritesheet.index = 0

