import sys
import random
import itertools

from ragtimerumble.config import (
    COUNTDOWNS, SMOOTH_PATH_SELECTION_RADIUS, SMOOTH_PATH_USAGE_PROBABILITY,
    HARD_PATH_SELECTION_RADIUS)
from ragtimerumble.config import (
    CHARACTER_STATUSES, HARD_PATH_USAGE_PROBABILITY)
from ragtimerumble.coordinates import path_cross_rect
from ragtimerumble.io import choice_death_sentence
from ragtimerumble.pathfinding import (
    shortest_path, smooth_path_to_path, equilateral_path,
    filter_close_paths, choice_destination)
from ragtimerumble.pilot import SmoothPathPilot, HardPathPilot


class Npc:
    """
    Fake player
    """

    def __init__(self, character, scene):
        self.character = character
        self.scene = scene
        self.next_duel_check_countdown = self.get_next_duel_check_countdown()
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

        self.next_duel_check_countdown = self.get_next_duel_check_countdown()
        self.release_time = random.randrange(
            COUNTDOWNS.DUEL_RELEASE_TIME_MIN,
            COUNTDOWNS.DUEL_RELEASE_TIME_MAX)
        return True

    def get_next_duel_check_countdown(self):
        chr_num = self.scene.alive_character_number
        minimum = COUNTDOWNS.DUEL_RELEASE_TIME_MIN * (chr_num / 10)
        maximum = COUNTDOWNS.DUEL_RELEASE_TIME_MAX * (chr_num / 2)
        return random.randrange(int(minimum), int(maximum))

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
        name = self.character.display_name
        messenger = self.scene.messenger
        sentence = choice_death_sentence()
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

