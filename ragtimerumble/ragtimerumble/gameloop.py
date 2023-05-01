import random
import pygame
from copy import deepcopy
from ragtimerumble import preferences
from ragtimerumble.io import (
    list_joysticks, stop_ambiance, play_dispatcher_music, quit_event,
    stop_sound, play_sound, get_current_commands, stop_scene_music,
    stop_dispatcher_music, play_scene_music)
from ragtimerumble.config import LOOP_STATUSES, COUNTDOWNS, DIRECTIONS
from ragtimerumble.menu import Menu
from ragtimerumble.scene import load_scene, populate_scene, depopulate_scene
from ragtimerumble.player import Player
from ragtimerumble.npc import Npc


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


class GameLoop:
    def __init__(self):
        self.status = LOOP_STATUSES.MENU
        self.scene_path = None
        self.scene = None
        self.dispatcher = None
        self.done = False
        self.clock = pygame.time.Clock()
        self.scores = deepcopy(VIRGIN_SCORES)
        self.joysticks = list_joysticks()
        self.menu = Menu(self.joysticks)

    def set_scene(self, path):
        self.scene_path = path
        self.scene = load_scene(path)

    def start_scene(self, start_music=True):
        gametype = preferences.get('gametype')
        populate_scene(self.scene_path, self.scene, gametype=gametype)
        self.status = LOOP_STATUSES.DISPATCHING
        self.dispatcher = PlayerDispatcher(self.scene, self.joysticks)
        stop_ambiance()
        if start_music:
            play_dispatcher_music()

    def __next__(self):
        self.done = self.done or quit_event()
        if self.done:
            return

        match self.status:
            case LOOP_STATUSES.MENU:
                next(self.menu)
                if self.menu.done is True:
                    self.done = True
                    return
                if self.menu.start is True:
                    self.start_scene(start_music=False)
                self.clock.tick(60)

            case LOOP_STATUSES.BATTLE:
                next(self.scene)
                self.clock.tick(60)
                if self.scene.ultime_showdown:
                    stop_sound(self.scene.ambiance)
                    stop_scene_music()
                    self.status = LOOP_STATUSES.LAST_KILL

            case LOOP_STATUSES.DISPATCHING:
                next(self.dispatcher)
                self.clock.tick(60)
                if self.dispatcher.done:
                    stop_dispatcher_music()
                    self.start_game()

            case LOOP_STATUSES.LAST_KILL:
                self.clock.tick(30)
                next(self.scene)
                if self.scene.done:
                    self.show_score()

            case LOOP_STATUSES.SCORE:
                for joystick in self.joysticks:
                    if get_current_commands(joystick).get("A"):
                        depopulate_scene(self.scene)
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
        play_sound(self.scene.ambiance, -1)
        play_scene_music(self.scene.musics)


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
                    play_sound('resources/sounds/coltclick.wav')
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
                play_sound('resources/sounds/stroke_whoosh_02.ogg')
                self.joysticks_column[i] = value
                self.cooldowns[i] = COUNTDOWNS.MENU_SELECTION_COOLDOWN

            elif get_current_commands(joystick).get('RIGHT'):
                play_sound('resources/sounds/stroke_whoosh_02.ogg')
                value = min((4, self.joysticks_column[i] + 1))
                self.joysticks_column[i] = value
                self.cooldowns[i] = COUNTDOWNS.MENU_SELECTION_COOLDOWN

            elif get_current_commands(joystick).get('A'):
                column = self.joysticks_column[i]
                if column == 2:
                    continue
                if self.assigned[column] is None:
                    self.assigned[column] = joystick
                    self.generate_characters(column)
                play_sound('resources/sounds/card.wav')

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