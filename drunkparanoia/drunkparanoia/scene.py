import json
import random
from drunkparanoia.background import Prop
from drunkparanoia.character import Character, Player, Npc
from drunkparanoia.coordinates import box_hit_box
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
    spots = data['popspot'][:]
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
    return scene


class Scene:

    def __init__(self):
        self.name = ""
        self.elements = []
        self.players = []
        self.npcs = []
        self.possible_duels = []

    @property
    def characters(self):
        return [elt for elt in self.elements if isinstance(elt, Character)]

    def collide_prop(self, box):
        for element in self.elements:
            if not isinstance(element, Prop):
                continue
            if box_hit_box(box, element.screen_box):
                return True
        return False

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


