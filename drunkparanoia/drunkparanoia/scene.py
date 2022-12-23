import sys
import json
import random
import itertools

from drunkparanoia.background import Prop, Background, Overlay
from drunkparanoia.character import Character, Player, Npc
from drunkparanoia.coordinates import (
    box_hit_box, point_in_rectangle, box_hit_polygon, path_cross_polygon,
    path_cross_rect)
from drunkparanoia.config import DIRECTIONS, GAMEROOT, COUNTDOWNS
from drunkparanoia.duel import find_possible_duels
from drunkparanoia.io import load_image, load_data
from drunkparanoia.sprite import SpriteSheet


def load_scene(filename):

    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        data = json.load(f)
    scene = Scene()
    scene.name = data['name']
    scene.no_go_zones = data['no_go_zones']
    scene.walls = data['walls']
    scene.stairs = data['stairs']
    scene.targets = data['targets']
    scene.fences = data['fences']
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
        prop = Prop(image, position, center, box, scene)
        scene.props.append(prop)

    spots = data['popspots'][:]
    random.shuffle(spots)
    spots = itertools.cycle(spots)
    characters = itertools.cycle(data['characters'])
    for _ in range(data['character_number']):
        character = next(characters)
        position = next(spots)
        spritesheet = SpriteSheet(load_data(character['file']))
        directions = DIRECTIONS.LEFT, DIRECTIONS.RIGHT
        character = Character(position, spritesheet, scene)
        character.direction = random.choice(directions)
        scene.characters.append(character)

    for interaction_zone in data['interactions']:
        zone = InteractionZone(interaction_zone)
        scene.interaction_zones.append(zone)
    return scene


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

    def assign_player(self, index, joystick):
        characters = self.characters
        for player in self.players:
            for character in characters:
                if player.character == character:
                    msg = f'Character {index} already assigned to player'
                    raise ValueError(msg)

        player = Player(self.characters[index], joystick)
        self.players.append(player)

    def create_npcs(self):
        assigned_characters = [player.character for player in self.players]
        for character in self.characters:
            if character in assigned_characters:
                continue
            self.npcs.append(Npc(character))

    def apply_black_screen(self, character):
        # if character not in [p.character for p in self.players]:
        #     return False
        self.black_screen_countdown = COUNTDOWNS.BLACK_SCREEN_COUNT_DOWN
        return True

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
