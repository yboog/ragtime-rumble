import json
import random

from drunkparanoia.background import Prop, Background
from drunkparanoia.character import Character, Player, Npc
from drunkparanoia.coordinates import box_hit_box, point_in_rectangle, box_hit_polygon
from drunkparanoia.config import DIRECTIONS, GAMEROOT, ELEMENT_TYPES
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

    for background in data['backgrounds']:
        image = load_image(background['file'])
        position = background['position']
        scene.backgrounds.append(Background(image=image, position=position))

    spots = data['popspots'][:]
    random.shuffle(spots)
    spots = iter(spots)

    for element in data['elements']:
        if element['type'] == ELEMENT_TYPES.PROP:
            image = load_image(element['file'], (0, 255, 0))
            position = element['position']
            center = element['center']
            box = element['box']
            prop = Prop(image, position, center, box, scene)
            scene.elements.append(prop)
        elif element['type'] == ELEMENT_TYPES.CHARACTER:
            position = next(spots)
            spritesheet = SpriteSheet(load_data(element['file']))
            directions = DIRECTIONS.LEFT, DIRECTIONS.RIGHT
            character = Character(position, spritesheet, scene)
            character.direction = random.choice(directions)
            scene.elements.append(character)

    for interaction_zone in data['interactions']:
        zone = InteractionZone(interaction_zone)
        scene.interaction_zones.append(zone)
    return scene


class Scene:

    def __init__(self):
        self.name = ""
        self.elements = []
        self.players = []
        self.npcs = []
        self.possible_duels = []
        self.no_go_zones = []
        self.interaction_zones = []
        self.backgrounds = []
        self.walls = []
        self.stairs = []
        self.targets = []

    @property
    def characters(self):
        return [elt for elt in self.elements if isinstance(elt, Character)]

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


class InteractionZone:
    def __init__(self, data):
        self.target = data["target"]
        self.action = data["action"]
        self.zone = data["zone"]
        self.direction = data["direction"]

    def contains(self, position):
        return point_in_rectangle(position, *self.zone)
