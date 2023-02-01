import sys
import json
import random
import pygame
import itertools
from copy import deepcopy

from drunkparanoia.background import Prop, Background, Overlay
from drunkparanoia.character import Character
from drunkparanoia.coordinates import (
    box_hit_box, point_in_rectangle, box_hit_polygon, path_cross_polygon,
    path_cross_rect)
from drunkparanoia.config import (
    DIRECTIONS, GAMEROOT, COUNTDOWNS, LOOP_STATUSES, CHARACTER_STATUSES,
    MAX_MESSAGES, VARIANTS_COUNT)
from drunkparanoia.duel import find_possible_duels
from drunkparanoia.io import (
    load_image, load_data, quit_event, list_joysticks, image_mirror,
    choice_kill_sentence, choice_random_name, play_sound, stop_sound,
    stop_ambiance)
from drunkparanoia.joystick import get_current_commands
from drunkparanoia.npc import Npc, Pianist, Barman
from drunkparanoia.player import Player
from drunkparanoia.sprite import SpriteSheet


VIRGIN_SCORES = {
    'player 1': {
        'player 2': [0, 0],
        'player 3': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'victory': 0
    },
    'player 2': {
        'player 1': [0, 0],
        'player 3': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'victory': 0
    },
    'player 3': {
        'player 1': [0, 0],
        'player 2': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'victory': 0
    },
    'player 4': {
        'player 1': [0, 0],
        'player 2': [0, 0],
        'player 3': [0, 0],
        'civilians': 0,
        'victory': 0
    }
}

NPC_TYPES = {
    'pianist': Pianist,
    'barman': Barman
}


def get_score_data(scores, row, col):
    row_keys = list(VIRGIN_SCORES)
    col_keys = (
        'player 1',
        'player 2',
        'player 3',
        'player 4',
        'total',
        'civilians',
        'victory')
    if col_keys[col] == 'total':
        data = [scores[row_keys[row]].get(col_keys[i]) for i in range(4)]
        data = [d for d in data if d is not None]
        return [sum(d[0] for d in data), sum(d[1] for d in data)]
    return scores[row_keys[row]].get(col_keys[col])


def load_scene(filename):

    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        data = json.load(f)
    scene = Scene()
    scene.ambiance = data['ambiance']
    scene.music = data['music']
    scene.character_number = data['character_number']
    scene.name = data['name']
    scene.vfx = data['vfx']
    scene.no_go_zones = data['no_go_zones']
    scene.walls = data['walls']
    scene.stairs = data['stairs']
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

    for npc in data['npcs']:
        scene.secondary_npcs.append(NPC_TYPES[npc['type']](**npc))

    for interaction_zone in data['interactions']:
        zone = InteractionZone(interaction_zone)
        scene.interaction_zones.append(zone)

    return scene


class GameLoop:
    def __init__(self):
        self.status = LOOP_STATUSES.AWAITING
        self.scene_path = None
        self.scene = None
        self.dispatcher = None
        self.done = False
        self.clock = pygame.time.Clock()
        self.scores = deepcopy(VIRGIN_SCORES)
        self.joysticks = list_joysticks()

    def set_scene(self, path):
        self.scene_path = path

    def start_scene(self):
        self.scene = load_scene(self.scene_path)
        self.status = LOOP_STATUSES.DISPATCHING
        self.dispatcher = PlayerDispatcher(self.scene, self.joysticks)
        stop_ambiance()
        play_sound('resources/sounds/dispatcher_sound.ogg')

    def __next__(self):
        self.done = self.done or quit_event()
        if self.done:
            return
        match self.status:
            case LOOP_STATUSES.BATTLE:
                next(self.scene)
                self.clock.tick(60)
                if self.scene.ultime_showdown:
                    stop_sound(self.scene.ambiance)
                    stop_sound(self.scene.music)
                    self.status = LOOP_STATUSES.LAST_KILL

            case LOOP_STATUSES.DISPATCHING:
                next(self.dispatcher)
                self.clock.tick(60)
                if self.dispatcher.done:
                    stop_sound('resources/sounds/dispatcher_sound.ogg')
                    self.start_game()

            case LOOP_STATUSES.LAST_KILL:
                self.clock.tick(30)
                next(self.scene)
                if self.scene.done:
                    self.show_score()

            case LOOP_STATUSES.SCORE:
                for joystick in self.joysticks:
                    if get_current_commands(joystick).get("A"):
                        self.start_scene()
                self.clock.tick(10)

    def show_score(self):
        self.status = LOOP_STATUSES.SCORE
        for player in self.scene.players:
            player_key = f'player {player.index + 1}'
            if not player.dead:
                self.scores[player_key]['victory'] += 1
            if player.killer is not None:
                killer_key = f'player {player.killer + 1}'
                self.scores[killer_key][player_key][0] += 1
                self.scores[player_key][killer_key][1] += 1
            self.scores[player_key]['civilians'] += player.npc_killed

    @property
    def tick_time(self):
        return 30 if self.status == LOOP_STATUSES.LAST_KILL else 60

    def start_game(self):
        while len(self.scene.characters) < self.scene.character_number:
            self.scene.build_character()
        self.scene.create_npcs()
        self.status = LOOP_STATUSES.BATTLE
        import time
        time.sleep(0.1)
        play_sound(self.scene.ambiance)
        play_sound(self.scene.music)


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
        for j, direction in enumerate(('LEFT', 'RIGHT', 'UP', 'DOWN')):
            if get_current_commands(joystick).get(direction):
                character = self.characters[group][j]
                player = Player(character, joystick, i, self.scene)
                self.scene.players.append(player)
                self.players[i] = player
                for k in range(4):
                    if j == k:
                        continue
                    npc = Npc(self.characters[group][k], self.scene)
                    npc.interaction_loop_cooldown = random.choice(range(
                        COUNTDOWNS.INTERACTION_LOOP_COOLDOWN_MIN,
                        COUNTDOWNS.INTERACTION_LOOP_COOLDOWN_MAX))
                    self.scene.npcs.append(npc)
                return

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
            self.scene.build_character(group, direction, popspot_key)
            for popspot_key, direction in directions.items()]


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
        # Score
        self.bullet_positions = []
        self.bullet_images = []
        self.life_images = []
        self.life_positions = []
        self.score_ol = None
        # Data
        self.backgrounds = []
        self.characters = []
        self.fences = []
        self.hard_paths = []
        self.interaction_zones = []
        self.no_go_zones = []
        self.npcs = []
        self.overlays = []
        self.players = []
        self.possible_duels = []
        self.props = []
        self.secondary_npcs = []
        self.smooth_paths = []
        self.stairs = []
        self.targets = []
        self.vfx = []
        self.walls = []
        # Runtime
        self.black_screen_countdown = 0
        self.white_screen_countdown = 0
        self.killer = None
        self.popspot_generator = None
        self.character_generator = None
        self.messenger = Messenger()

    def create_vfx(self, name, position, flipped=True):
        for vfx in self.vfx:
            if vfx.get('type') != 'static' or vfx.get('name') != name:
                continue
            image = load_image(vfx['file'])
            if flipped:
                image = image_mirror(image, horizontal=True)
            self.overlays.append(Overlay(image, position, vfx['y']))
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

    def build_character(self, group=None, direction=None, popspot=None):
        if group and popspot:
            position = group['popspots'][popspot]
        else:
            position = next(self.popspot_generator)
            direction = direction or random.choice(DIRECTIONS.ALL)
        char = next(self.character_generator)
        data = load_data(char)
        spritesheet = SpriteSheet(data)
        variation = random.choice(list(range(VARIANTS_COUNT)))
        char = Character(position, spritesheet, variation, self)
        char.gender = data['gender']
        if group:
            zone = self.get_interaction(group['interactions'][direction])
            zone.busy = zone
            char.interacting_zone = zone
            char.spritesheet.animation = zone.action
            char.current_interaction = zone.id
            char.status = CHARACTER_STATUSES.INTERACTING
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
        index = int(round((score / COUNTDOWNS.MAX_LIFE) * 3))
        return self.life_images[player_n][index]

    def bullet_image(self, player_n, on=True):
        return self.bullet_images[player_n][0 if on else 1]

    @property
    def elements(self):
        return self.characters + self.props + self.overlays + self.secondary_npcs

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

    def find_player(self, character):
        for player in self.players:
            if player.character == character:
                return player

    def kill_message(self, killer, victim):
        pl = self.find_player(killer)
        name1 = f'Player {pl.index + 1}' if pl else choice_random_name(killer.gender)
        pl = self.find_player(victim)
        name2 = f'Player {pl.index + 1}' if pl else choice_random_name(victim.gender)
        msg = choice_kill_sentence('french')
        self.messenger.add_message(f'{name1} {msg} {name2}')

    def create_npcs(self):
        assigned_characters = [player.character for player in self.players]
        assigned_characters += [npc.character for npc in self.npcs]
        for character in self.characters:
            if character in assigned_characters:
                continue
            self.npcs.append(Npc(character, self))

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
    def dying_characters(self):
        return [
            c for c in self.characters if c.spritesheet.animation == 'death']


class Messenger:
    def __init__(self):
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
        if countdown > COUNTDOWNS.MESSAGE_FADEOFF_DURATION:
            return 255
        return int((countdown / COUNTDOWNS.MESSAGE_FADEOFF_DURATION) * 255)


class InteractionZone:
    def __init__(self, data):
        self.id = data['id']
        self.target = data["target"]
        self.action = data["action"]
        self.zone = data["zone"]
        self.attraction = data["attraction"]
        self.direction = data["direction"]
        self.busy = False

    def contains(self, position):
        return point_in_rectangle(position, *self.zone)

    def attract(self, position):
        return point_in_rectangle(position, *self.attraction)
