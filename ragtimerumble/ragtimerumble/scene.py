import os
import sys
import uuid
import json
import random
import itertools
from random import shuffle
from copy import deepcopy

from ragtimerumble.background import Prop, Background, Overlay
from ragtimerumble.character import Character
from ragtimerumble.config import GAMEROOT
from ragtimerumble.coordinates import (
    box_hit_box, point_in_rectangle, box_hit_polygon, path_cross_polygon,
    path_cross_rect, Coordinates)
from ragtimerumble.config import (
    DIRECTIONS, GAMEROOT, COUNTDOWNS, CHARACTER_STATUSES,
    MAX_MESSAGES, PALLETTES_COUNT)
from ragtimerumble.duel import find_possible_duels
from ragtimerumble.io import (
    load_image, load_data, image_mirror, choice_display_name,
    choice_kill_sentence, load_frames)
from ragtimerumble.npc import Npc, Pianist, Barman, Sniper, Dog, Chicken
from ragtimerumble.sprite import SpriteSheet, image_index_from_exposures


NPC_TYPES = {
    'chicken': Chicken,
    'pianist': Pianist,
    'barman': Barman,
    'sniper': Sniper,
    'dog': Dog,
}


def scene_iterator():
    scene_filepaths = [
        f'resources/scenes/{f}'
        for f in os.listdir(f'{GAMEROOT}/resources/scenes')
        if not f.startswith('_')]
    shuffle(scene_filepaths)
    return itertools.cycle(scene_filepaths)


def load_scene(filename):
    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        data = json.load(f)
    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        data = json.load(f)
    scene = Scene(data)
    scene.ambiance = data['ambiance']
    scene.musics = data['musics']
    scene.character_number = data['character_number']
    scene.name = data['name']
    scene.vfx = data['vfx']
    scene.no_go_zones = data['no_go_zones']
    scene.walls = data['walls']
    scene.stairs = data['stairs']
    scene.shadow_zones = data['shadow_zones']
    scene.targets = data['targets']
    scene.fences = data['fences']
    scene.startups = data['startups']
    scene.smooth_paths = [p['points'] for p in data['paths'] if not p['hard']]
    scene.hard_paths = [p['points'] for p in data['paths'] if p['hard']]
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

    return scene


def depopulate_scene(scene, clear_players=True):
    if clear_players:
        scene.players.clear()
        scene.bullet_positions.clear()
        scene.life_positions.clear()
        scene.life_images.clear()
        scene.bullet_images.clear()
    scene.secondary_npcs.clear()
    scene.interaction_zones.clear()
    scene.possible_duels.clear()
    scene.characters.clear()
    scene.sniperreticles.clear()
    scene.black_screen_countdown = 0
    scene.white_screen_countdown = 0
    scene.animated_vfx.clear()
    scene.messenger.clear()
    scene.vfx_overlays.clear()
    scene.npcs.clear()


def populate_scene(filename, scene, gametype):
    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        data = json.load(f)

    for i in range(1, 5):
        player_key = f'player{i}'
        position = data['score'][player_key]['life']['position']
        scene.life_positions.append(position)
        scene.life_images.append([
            load_image(data['score'][player_key]['life'][f'file{j}'])
            for j in range(1, 5)])
        position = data['score'][player_key]['bullet']['position']
        scene.bullet_positions.append(position)
        on = load_image(data['score'][player_key]['bullet']['on'])
        off = load_image(data['score'][player_key]['bullet']['off'])
        scene.bullet_images.append([on, off])

    for npc in data['npcs']:
        if gametype not in npc['gametypes']:
            continue
        scene.secondary_npcs.append(NPC_TYPES[npc['type']](scene=scene, **npc))

    for interaction_zone in data['interactions']:
        if gametype not in interaction_zone['gametypes']:
            continue
        zone = InteractionZone(interaction_zone)
        scene.interaction_zones.append(zone)

    return scene


def find_prop(data, name):
    for prop in data['interactive_props']:
        if name == prop['name']:
            return prop
    raise ValueError(f'No prop found for type "{name}".')


class Scene:

    def __init__(self, data):
        self.data = data
        self.name = ""
        # Score
        self.bullet_positions = []
        self.bullet_images = []
        self.life_images = []
        self.life_positions = []
        self.score_ol = None
        # Data
        self.animated_vfx = []
        self.backgrounds = []
        self.characters = []
        self.fences = []
        self.hard_paths = []
        self.interaction_zones = []
        self.interactive_props = []
        self.no_go_zones = []
        self.npcs = []
        self.musics = []
        self.overlays = []
        self.players = []
        self.possible_duels = []
        self.props = []
        self.secondary_npcs = []
        self.smooth_paths = []
        self.shadow_zones = []
        self.sniperreticles = []
        self.stairs = []
        self.targets = []
        self.vfx = []
        self.vfx_overlays = []
        self.walls = []
        # Runtime
        self.black_screen_countdown = 0
        self.white_screen_countdown = 0
        self.killer = None
        self.popspot_generator = None
        self.character_generator = None
        self.messenger = Messenger()

    def coins_position(self, index):
        return self.data['score'][f'player{index + 1}']['coins_position']

    def create_vfx(self, name, position, flipped=True):
        for vfx in self.vfx:
            if vfx.get('type') == 'static' and vfx.get('name') == name:
                image = load_image(vfx['file'])
                if flipped:
                    image = image_mirror(image, horizontal=True)
                self.vfx_overlays.append(Overlay(image, position, vfx['y']))
                return
            if vfx.get('type') == 'animated' and vfx.get('name') == name:
                data = load_data(vfx['file'])
                self.animated_vfx.append(Vfx(data, position))
                return

    @property
    def done(self):
        return sum(True for p in self.players if not p.dead) == 1

    @property
    def ultime_showdown(self):
        if self.done:
            return False
        return sum(
            True for p in self.players if (not p.dead and not p.dying)) == 1

    @property
    def this_is_a_tie(self):
        return all(p.dead for p in self.players)

    def build_character(self, group=None, direction=None, popspot=None):
        if group and popspot:
            position = group['popspots'][popspot]
        else:
            position = next(self.popspot_generator)
            direction = direction or random.choice(DIRECTIONS.ALL)

        char = next(self.character_generator)
        data = load_data(char)
        spritesheet = SpriteSheet(data)
        palette = random.choice(list(range(PALLETTES_COUNT)))
        display_name = choice_display_name(data)
        char = Character(position, spritesheet, palette, display_name, self)

        if group:
            zone = self.get_interaction(group['interactions'][direction])
            apply_zone_to_character(zone, char)

        char.direction = direction
        self.characters.append(char)
        return char

    def get_interaction(self, interaction_id):
        for interaction in self.interaction_zones:
            if interaction.id == interaction_id:
                return interaction
        raise ValueError(
            f'{interaction_id} not found in '
            f'{[it.id for it in self.interaction_zones]}')

    def life_image(self, player_n, score):
        from math import ceil
        index = int(ceil((score / COUNTDOWNS.MAX_LIFE) * 3))
        index = min((index, 3))
        return self.life_images[player_n][index]

    def bullet_image(self, player_n, on=True):
        return self.bullet_images[player_n][0 if on else 1]

    @property
    def elements(self):
        return (
            self.characters + self.props + self.overlays +
            self.secondary_npcs + self.interactive_props +
            self.vfx_overlays + self.animated_vfx)

    def inclination_at(self, point):
        return next((
            stair['inclination']
            for stair in self.stairs
            if point_in_rectangle(point, *stair['zone'])),
            0)

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

    def instersected_shadow_zone(self, box):
        for shadow_zone in self.shadow_zones:
            if box_hit_polygon(box, shadow_zone['polygon']):
                return shadow_zone

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
        next(self.messenger)
        for evaluable in self.npcs + self.players + self.secondary_npcs:
            next(evaluable)

        if self.black_screen_countdown or self.white_screen_countdown:
            if self.white_screen_countdown:
                self.white_screen_countdown -= 1
            else:
                self.black_screen_countdown -= 1
            self.possible_duels = []
            return
        self.possible_duels = find_possible_duels(self)
        to_delete = []
        for vfx in self.animated_vfx:
            if vfx.type == 'static':
                continue
            if vfx.animation_is_done:
                to_delete.append(vfx)
                continue
            next(vfx)
        for vfx in to_delete:
            self.animated_vfx.remove(vfx)

    @property
    def snipers(self):
        return [npc for npc in self.secondary_npcs if isinstance(npc, Sniper)]

    def find_player(self, character):
        for player in self.players:
            if player.character == character:
                return player

    def kill_message(self, killer, victim):
        name1 = killer.display_name
        name2 = victim.display_name
        msg = choice_kill_sentence()
        self.messenger.add_message(f'{name1} {msg} {name2}')

    def create_npcs(self):
        assigned_characters = [player.character for player in self.players]
        assigned_characters += [npc.character for npc in self.npcs]
        for character in self.characters:
            if character in assigned_characters:
                continue
            self.npcs.append(Npc(character, self))

    def create_interactive_prop(self, position, name):
        prop = find_prop(self.data, name)
        zone = create_interactive_prop(prop, position)
        self.interactive_props.append(zone)

    def apply_black_screen(self, origin, target):
        self.white_screen_countdown = COUNTDOWNS.WHITE_SCREEN
        for player in self.players:
            if player.character == target:
                self.killer = None
                self.black_screen_countdown = COUNTDOWNS.BLACK_SCREEN
                return True
        self.killer = origin
        return False

    def apply_white_screen(self, origin):
        self.white_screen_countdown = COUNTDOWNS.WHITE_SCREEN
        self.killer = origin

    @property
    def alive_character_number(self):
        return len(
            [c for c in self.characters if c.status != CHARACTER_STATUSES.OUT])

    @property
    def dying_characters(self):
        return [
            c for c in self.characters if c.spritesheet.animation == 'death']

    def destroy(self, id_):
        for i, zone in enumerate(self.interactive_props):
            if zone.id == id_:
                break
        else:
            return
        del self.interactive_props[i]


def apply_zone_to_character(zone, character):
    zone.busy = zone
    character.interacting_zone = zone
    character.spritesheet.animation = zone.action
    character.current_interaction = zone.id
    character.status = CHARACTER_STATUSES.INTERACTING


class Messenger:
    def __init__(self):
        self.messages = []

    def clear(self):
        self.messages = []

    def add_message(self, message):
        self.messages.append([message, COUNTDOWNS.MESSAGE_DISPLAY_TIME])
        self.messages = self.messages[-MAX_MESSAGES:]

    def __next__(self):
        to_delete = []
        for i, message in enumerate(self.messages):
            if message[1] > 0:
                message[1] -= 1
            else:
                to_delete.append(i)
        for i in sorted(to_delete, reverse=True):
            del self.messages[i]

    @property
    def data(self):
        return [
            [text, self.get_opacity(countdown)]
            for text, countdown in self.messages]

    def get_opacity(self, countdown):
        if countdown > COUNTDOWNS.MESSAGE_FADEOFF_EXPOSURE:
            return 255
        return int((countdown / COUNTDOWNS.MESSAGE_FADEOFF_EXPOSURE) * 255)


def create_interactive_prop(prop, position):
    prop = deepcopy(prop)
    position = list(position)
    position[0] += prop['offset'][0]
    position[1] += prop['offset'][1]
    prop['zone'][0] += position[0]
    prop['zone'][1] += position[1]
    prop['target'][0] += position[0]
    prop['target'][1] += position[1]
    prop['id'] = uuid.uuid1()
    prop['busy'] = False
    zone = InteractionZone(prop)
    zone.switch = prop['switch'] + position[1]
    zone.image = load_image(prop['image'])
    zone.render_position = position
    zone.attraction[0] += position[0]
    zone.attraction[1] += position[1]
    zone.destroyable = True
    return zone


class InteractionZone:
    def __init__(self, data):
        self.data = data
        self.id = data['id']
        self.in_sound = data['insound']
        self.out_sound = data['outsound']
        self.target = data["target"]
        self.action = data["action"]
        self.zone = data["zone"]
        self.attraction = data["attraction"]
        self.direction = data["direction"]
        self.enable = True
        self.play_once = data["play_once"]
        self.busy = False
        self.destroyable = False

    @property
    def lockable(self):
        return self.data['lockable']

    def contains(self, position):
        return point_in_rectangle(position, *self.zone)

    def attract(self, position):
        return point_in_rectangle(position, *self.attraction)


class Vfx:
    def __init__(self, data, position):
        self.id = uuid.uuid1()
        self.index = 0
        self.type = data['type']
        self.images = load_frames(data['sheet'], data['framesize'], None)
        self.coordinates = Coordinates(position)
        self.exposures = data['exposures']
        self.switch = 2000

    @property
    def render_position(self):
        return self.coordinates.position

    def __next__(self):
        if self.animation_is_done:
            return
        self.index += 1

    @property
    def image(self):
        index = image_index_from_exposures(self.index, self.exposures)
        return self.images[index]

    @property
    def animation_is_done(self):
        return self.index >= sum(self.exposures) - 1
