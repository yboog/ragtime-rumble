import sys
import json
import random
import pygame

import itertools

from drunkparanoia.background import Prop, Background, Overlay
from drunkparanoia.character import Character, Player, Npc
from drunkparanoia.coordinates import (
    box_hit_box, point_in_rectangle, box_hit_polygon, path_cross_polygon,
    path_cross_rect)
from drunkparanoia.config import (
    DIRECTIONS, GAMEROOT, COUNTDOWNS, LOOP_STATUSES)
from drunkparanoia.duel import find_possible_duels
from drunkparanoia.io import load_image, load_data, quit_event, list_joysticks
from drunkparanoia.joystick import get_current_commands
from drunkparanoia.sprite import SpriteSheet


def load_scene(filename):

    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        data = json.load(f)
    scene = Scene()
    scene.character_number = data['character_number']
    scene.name = data['name']
    scene.no_go_zones = data['no_go_zones']
    scene.walls = data['walls']
    scene.stairs = data['stairs']
    scene.targets = data['targets']
    scene.fences = data['fences']
    scene.startups = data['startups']
    popspots = data['popspots'][:]
    random.shuffle(popspots)
    scene.popspot_generator = itertools.cycle(popspots)
    scene.character_generator = itertools.cycle(data['characters'])

    position = data['score']['ol']['position']
    image = load_image(data['score']['ol']['file'], key_color=(0, 255, 0))
    scene.score_ol = Overlay(image, position, sys.maxsize)

    for background in data['backgrounds']:
        image = load_image(background['file'])
        position = background['position']
        scene.backgrounds.append(Background(image=image, position=position))

    for i in range(1, 5):
        player_key = f'player{i}'
        scene.score_positions.append(data['score'][player_key]['position'])
        scene.score_images.append([
            load_image(data['score'][player_key][f'file{j}'])
            for j in range(1, 5)])

    for ol in data['overlays']:
        image = load_image(ol['file'], (0, 255, 0))
        scene.overlays.append(Overlay(image, ol['position'], ol['y']))

    for prop in data['props']:
        image = load_image(prop['file'])
        position = prop['position']
        center = prop['center']
        box = prop['box']
        visible_at_dispatch = prop['visible_at_dispatch']
        prop = Prop(image, position, center, box, visible_at_dispatch, scene)
        scene.props.append(prop)

    for interaction_zone in data['interactions']:
        zone = InteractionZone(interaction_zone)
        scene.interaction_zones.append(zone)

    return scene


class GameLoop:
    def __init__(self):
        self.status = LOOP_STATUSES.AWAITING
        self.scene = None
        self.dispatcher = None
        self.done = False
        self.clock = pygame.time.Clock()

    def start_scene(self, scene):
        self.status = LOOP_STATUSES.DISPATCHING
        self.dispatcher = PlayerDispatcher(scene, list_joysticks())
        self.scene = scene

    def __next__(self):
        self.done = self.done or quit_event()
        if self.done:
            return

        match self.status:
            case LOOP_STATUSES.BATTLE:
                next(self.scene)
                self.clock.tick(60)

            case LOOP_STATUSES.DISPATCHING:
                next(self.dispatcher)
                self.clock.tick(60)
                if self.dispatcher.done:
                    self.start_game()

    def start_game(self):
        while len(self.scene.characters) <= self.scene.character_number:
            self.scene.build_character()
        self.scene.create_npcs()
        self.status = LOOP_STATUSES.BATTLE


class PlayerDispatcher:

    def __init__(self, scene, joysticks):
        self.done = False
        self.scene = scene
        self.joysticks = joysticks
        self.joysticks_column = [2] * len(joysticks)
        self.characters = [None, None, None, None]
        self.cooldowns = [0, 0, 0, 0]
        self.assigned = [None, None, None, None, None]
        self.players = [None for _ in range(len(joysticks))]

    def eval_player_selection(self, i, joystick):
        group = column_to_group(self.joysticks_column[i])
        if get_current_commands(joystick).get('LEFT'):
            character = self.characters[group][0]
        elif get_current_commands(joystick).get('RIGHT'):
            character = self.characters[group][1]
        elif get_current_commands(joystick).get('UP'):
            character = self.characters[group][2]
        elif get_current_commands(joystick).get('DOWN'):
            character = self.characters[group][3]
        else:
            return
        player = Player(character, joystick, i, self.scene)
        self.scene.players.append(player)
        self.players[i] = player

    def __next__(self):
        if self.done:
            return

        for i, joystick in enumerate(self.joysticks):
            if self.cooldowns[i] > 0:
                self.cooldowns[i] -= 1
                continue

            if joystick in self.assigned:
                if not self.players[i]:
                    self.eval_player_selection(i, joystick)
                continue

            if get_current_commands(joystick).get('LEFT'):
                value = max((0, self.joysticks_column[i] - 1))
                self.joysticks_column[i] = value
                self.cooldowns[i] = 10

            elif get_current_commands(joystick).get('RIGHT'):
                value = min((4, self.joysticks_column[i] + 1))
                self.joysticks_column[i] = value
                self.cooldowns[i] = 10

            elif get_current_commands(joystick).get('A'):
                column = self.joysticks_column[i]
                if column == 2:
                    continue
                if self.assigned[column] is None:
                    self.assigned[column] = joystick
                    self.generate_characters(column)

        self.done = sum(bool(p) for p in self.players) == len(self.joysticks)

    def generate_characters(self, column):
        index = column_to_group(column)
        group = self.scene.startups['groups'][index]
        directions = {
            'left': DIRECTIONS.RIGHT,
            'right': DIRECTIONS.LEFT,
            'up': DIRECTIONS.DOWN,
            'down': DIRECTIONS.UP}

        self.characters[index] = [
            self.scene.build_character(group['popspots'][position], direction)
            for position, direction in directions.items()]


def column_to_group(column):
    """
    On dispatching screen, the column 2 is the unisgned one.
    To find the corresponding startups group, you need top map the column to
    the group and swallow the 2 index.
    """
    return column if column < 2 else column - 1


class Scene:

    def __init__(self):
        self.name = ""
        self.score_ol = None
        self.score_images = []
        self.score_positions = []
        self.characters = []
        self.props = []
        self.overlays = []
        self.players = []
        self.npcs = []
        self.possible_duels = []
        self.no_go_zones = []
        self.interaction_zones = []
        self.backgrounds = []
        self.walls = []
        self.stairs = []
        self.targets = []
        self.fences = []

        self.black_screen_countdown = 0
        self.popspot_generator = None
        self.character_generator = None

    def build_character(self, position=None, direction=None):
        position = position or next(self.popspot_generator)
        direction = direction or random.choice(DIRECTIONS.ALL)
        char = next(self.character_generator)
        spritesheet = SpriteSheet(load_data(char['file']))
        char = Character(position, spritesheet, char['variation'], self)
        char.direction = direction
        self.characters.append(char)
        return char

    def score_image(self, player_n, score):
        index = int(round((score / COUNTDOWNS.MAX_LIFE) * 3))
        return self.score_images[player_n][index]

    @property
    def elements(self):
        return self.characters + self.props + self.overlays

    def inclination_at(self, point):
        for stair in self.stairs:
            if point_in_rectangle(point, *stair['zone']):
                return stair['inclination']
        return 0

    def choice_destination_from(self, point):
        targets = [
            t for t in self.targets
            if point_in_rectangle(point, *t['origin'])]

        if not targets:
            return

        destinations = [
            d for t in targets
            for _ in range(t['weight'])
            for d in t['destinations']]

        destination = random.choice(destinations)
        x = random.randrange(destination[0], destination[0] + destination[2])
        y = random.randrange(destination[1], destination[1] + destination[3])

        return x, y

    def cross(self, path):
        for element in self.elements:
            if not isinstance(element, Prop) or not element.screen_box:
                continue
            if path_cross_rect(path, element.screen_box):
                return True
        if any(path_cross_rect(zone, path) for zone in self.no_go_zones):
            return True
        return any(path_cross_polygon(path, wall) for wall in self.walls)

    def collide(self, box):
        for element in self.elements:
            if not isinstance(element, Prop) or not element.screen_box:
                continue
            if box_hit_box(box, element.screen_box):
                return True
        if any(box_hit_box(zone, box) for zone in self.no_go_zones):
            return True
        return any(box_hit_polygon(box, wall) for wall in self.walls)

    def __next__(self):
        for evaluable in self.npcs + self.players:
            next(evaluable)

        if self.black_screen_countdown > 0:
            self.black_screen_countdown -= 1
            self.possible_duels = []
            return
        self.possible_duels = find_possible_duels(self)

    def find_player(self, character):
        for player in self.players:
            if player.character == character:
                return player

    def create_npcs(self):
        assigned_characters = [player.character for player in self.players]
        for character in self.characters:
            if character in assigned_characters:
                continue
            self.npcs.append(Npc(character, self))

    def apply_black_screen(self, character):
        for player in self.players:
            if player.character == character:
                self.black_screen_countdown = COUNTDOWNS.BLACK_SCREEN_COUNT_DOWN
                return True
        return False

    @property
    def dying_characters(self):
        return [
            c for c in self.characters if c.spritesheet.animation == 'death']


class InteractionZone:
    def __init__(self, data):
        self.target = data["target"]
        self.action = data["action"]
        self.zone = data["zone"]
        self.direction = data["direction"]

    def contains(self, position):
        return point_in_rectangle(position, *self.zone)
