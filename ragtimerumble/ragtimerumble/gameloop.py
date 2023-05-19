import random
import pygame
from copy import deepcopy
from ragtimerumble import preferences
from ragtimerumble.io import (
    list_joysticks, stop_ambiance, play_dispatcher_music, quit_event,
    stop_sound, play_sound, get_current_commands, stop_scene_music,
    stop_dispatcher_music, play_scene_music)
from ragtimerumble.config import (
    LOOP_STATUSES, COUNTDOWNS, DIRECTIONS, DEFAULT_SCENE)
from ragtimerumble.menu import (
    Menu, ScoreSheetScreen, PauseMenu, NavigationButton)
from ragtimerumble.scene import load_scene, populate_scene, depopulate_scene
from ragtimerumble.player import Player
from ragtimerumble.npc import Npc


VIRGIN_SCORES = {
    'round': 0,
    'player 1': {
        'player 2': [0, 0],
        'player 3': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 2': {
        'player 1': [0, 0],
        'player 3': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 3': {
        'player 1': [0, 0],
        'player 2': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 4': {
        'player 1': [0, 0],
        'player 2': [0, 0],
        'player 3': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
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
        self.scores_screen = None
        self.menu = Menu(self.joysticks)

    def reset_game(self):
        self.status = LOOP_STATUSES.MENU
        self.scene_path = None
        self.scene = None
        self.dispatcher = None
        self.done = False
        self.clock = pygame.time.Clock()
        self.scores = deepcopy(VIRGIN_SCORES)
        self.joysticks = list_joysticks()
        self.scores_screen = None
        self.menu = Menu(self.joysticks)
        self.menu.button_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN * 2
        self.set_scene(DEFAULT_SCENE)

    def set_scene(self, path):
        self.scene_path = path
        self.scene = load_scene(path)

    def start_scene(self, start_music=True):
        gametype = preferences.get('gametype')
        depopulate_scene(self.scene)
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
                    self.joysticks = list_joysticks()
                    self.start_scene(start_music=False)
                self.clock.tick(60)

            case LOOP_STATUSES.PAUSE:
                if self.pause_menu.done:
                    self.pause_menu = None
                    self.status = LOOP_STATUSES.BATTLE
                    return
                if self.pause_menu.back_to_menu:
                    self.reset_game()
                    stop_scene_music()
                    stop_ambiance()
                    cld = COUNTDOWNS.MENU_SELECTION_COOLDOWN * 2
                    self.menu.button_countdown = cld
                    return
                if self.pause_menu.quit_game:
                    self.done = True
                next(self.pause_menu)
                self.clock.tick(60)
                return

            case LOOP_STATUSES.BATTLE:
                for joystick in self.joysticks:
                    command = get_current_commands(joystick)
                    if command.get('start') is True:
                        self.status = LOOP_STATUSES.PAUSE
                        self.pause_menu = PauseMenu(self.joysticks)
                        return
                next(self.scene)
                self.clock.tick(60)
                if self.scene.ultime_showdown:
                    stop_sound(self.scene.ambiance)
                    stop_scene_music()
                    self.status = LOOP_STATUSES.LAST_KILL

            case LOOP_STATUSES.DISPATCHING:
                next(self.dispatcher)
                self.clock.tick(60)
                if self.dispatcher.back_to_menu:
                    self.reset_game()
                    return
                if self.dispatcher.done:
                    stop_dispatcher_music()
                    self.start_round()

            case LOOP_STATUSES.LAST_KILL:
                self.clock.tick(30)
                next(self.scene)
                if self.scene.done:
                    self.show_score()

            case LOOP_STATUSES.SCORE:
                next(self.scores_screen)
                if self.scores_screen.next_round is True:
                    self.start_scene()
                    self.clock.tick(60)
                if self.scores_screen.back_to_menu is True:
                    self.reset_game()

    def show_score(self):
        self.status = LOOP_STATUSES.SCORE
        winner = next((p.index for p in self.scene.players if not p.dead), -1)

        for player in self.scene.players:
            player_key = f'player {player.index + 1}'
            if not player.dead:
                self.scores[player_key]['victory'] += 1
            else:
                self.scores[player_key]['deaths'] += 1
            if player.killer is not None:
                killer_key = f'player {player.killer + 1}'
                self.scores[killer_key][player_key][0] += 1
                self.scores[player_key][killer_key][1] += 1
            self.scores[player_key]['civilians'] += player.npc_killed
            killed = [
                p for p in self.scene.players
                if p.killer == player.index]
            bank = (
                player.coins +
                (2 * len(killed)) +
                (3 if winner == player.index else 0) -
                (player.npc_killed * 2))
            self.scores[player_key]['money_earned'] += bank
            self.scores[player_key]['looted_bodies'] += player.looted_bodies

        self.scores_screen = ScoreSheetScreen(
            self.scene.players, winner, self.scores, self.joysticks)
        for player in self.scene.players:
            coord = self.scores_screen.characters_coordinates[player.index]
            player.character.coordinates = coord
        depopulate_scene(self.scene, clear_players=False)

    def start_round(self):
        while len(self.scene.characters) < self.scene.character_number:
            self.scene.build_character()
        self.scene.create_npcs()
        self.scores['round'] += 1
        self.status = LOOP_STATUSES.BATTLE
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
        self.leave_overlay = False
        self.back_to_menu = False
        self.back_to_menu_buttons = [
            NavigationButton('back_to_menu', 'A'),
            NavigationButton('no', 'B')]

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
                    joystick.rumble(1, 1, 1)
                return

    def __next__(self):
        if self.done:
            return

        for i, joystick in enumerate(self.joysticks):
            if self.cooldowns[i] > 0:
                self.cooldowns[i] -= 1
                continue

            commands = get_current_commands(joystick)

            if self.leave_overlay:
                return self.eval_leave_overlay(commands)

            if commands.get('B'):
                self.cooldowns[i] = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                self.leave_overlay = True

            if joystick in self.assigned:
                if not self.players[i]:
                    self.eval_player_selection(i, joystick)
                continue

            if commands.get('LEFT'):
                value = max((0, self.joysticks_column[i] - 1))
                play_sound('resources/sounds/stroke_whoosh_02.ogg')
                self.joysticks_column[i] = value
                self.cooldowns[i] = COUNTDOWNS.MENU_SELECTION_COOLDOWN

            elif commands.get('RIGHT'):
                play_sound('resources/sounds/stroke_whoosh_02.ogg')
                value = min((4, self.joysticks_column[i] + 1))
                self.joysticks_column[i] = value
                self.cooldowns[i] = COUNTDOWNS.MENU_SELECTION_COOLDOWN

            elif commands.get('A'):
                column = self.joysticks_column[i]
                if column == 2:
                    continue
                if self.assigned[column] is None:
                    self.assigned[column] = joystick
                    self.generate_characters(column)
                play_sound('resources/sounds/card.wav')

        self.done = sum(bool(p) for p in self.players) == len(self.joysticks)

    def eval_leave_overlay(self, commands):
        if commands.get('B'):
            self.leave_overlay = False
            for i in range(len(self.cooldowns)):
                self.cooldowns[i] = COUNTDOWNS.MENU_SELECTION_COOLDOWN
        if commands.get('A'):
            self.back_to_menu = True

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
