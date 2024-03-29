import random
from copy import deepcopy
from ragtimerumble import preferences
from ragtimerumble.config import (
    COUNTDOWNS, DIRECTIONS, AVAILABLE_LANGUAGES, GAMETYPES)
from ragtimerumble.display import set_screen_display_mode
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import (
    load_data, load_image, get_menu_text, play_sound, play_dispatcher_music,
    get_how_to_play_image, get_touch_button_image, build_winner_message)
from ragtimerumble.sprite import SpriteSheet
from ragtimerumble.joystick import get_pressed_direction, get_current_commands
from ragtimerumble.scores import get_final_winner_index, get_most_sheet
from ragtimerumble.display import is_fullscreen


def _get_current_screen_menu_value():
    if is_fullscreen():
        return 'fullscreen'
    return 'windowed'


class Menu:
    def __init__(self, joysticks):
        self.title = Title()
        self.joysticks = joysticks
        self.index = 0
        self.bg = load_image('resources/ui/title-bg.png')
        self.done = False
        self.start = False
        displays = ('fullscreen', 'wscaled', 'windowed')
        rounds = [f'{i}' for i in range(1, 11)]
        self.items = [
            EnumItem(
                0, 'new_game', (361, 185),
                values=('advanced', 'basic'),
                default=preferences.get('gametype')),
            EnumItem(
                1, 'display', (361, 210),
                values=displays,
                default=_get_current_screen_menu_value()),
            EnumItem(
                2, 'language', (361, 225),
                values=AVAILABLE_LANGUAGES,
                default=preferences.get('language')),
            EnumItem(
                3, 'rounds', (361, 240),
                values=rounds, default=f'{preferences.get("rounds")}'),
            MenuItem(4, 'controls', (361, 265)),
            MenuItem(5, 'help', (361, 280)),
            MenuItem(6, 'quit', (361, 305))]
        self.items[3].enum_index = 9
        self.direction_countdown = 0
        self.button_countdown = 0
        self.subscreen = None
        play_dispatcher_music()

    def __next__(self):
        if self.subscreen and not self.subscreen.done:
            next(self.subscreen)
            return

        if self.subscreen:
            self.subscreen = None

        next(self.title)
        if self.button_countdown > 0:
            self.button_countdown -= 1
            return

        for joystick in self.joysticks:
            commands = get_current_commands(joystick)
            if commands.get('A'):
                match self.index:
                    case 0:
                        self.start = True
                    case 4:
                        self.subscreen = ControlMenuScreen(self.joysticks)
                        return
                    case 5:
                        self.subscreen = HowToPlayScreen(self.joysticks)
                        return
                    case 6:
                        self.done = True
                        return

            if self.direction_countdown > 0:
                self.direction_countdown -= 1
                continue

            direction = get_pressed_direction(joystick)
            directions = (DIRECTIONS.LEFT, DIRECTIONS.RIGHT)
            enums = 0, 1, 2, 3
            if direction in directions and self.index in enums:
                self.items[self.index].set_next(direction == DIRECTIONS.LEFT)
                self.direction_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                match self.index:
                    case 0:
                        play_sound('resources/sounds/coltclick.wav')
                        i = self.items[0].enum_index
                        preferences.set('gametype', GAMETYPES[i])
                    case 1:
                        play_sound('resources/sounds/coltclick.wav')
                        self.update_display_mode()
                    case 2:
                        play_sound('resources/sounds/coltclick.wav')
                        i = self.items[2].enum_index
                        preferences.set('language', AVAILABLE_LANGUAGES[i])
                    case 3:
                        play_sound('resources/sounds/coltclick.wav')
                        i = self.items[3].enum_index
                        preferences.set('rounds', int(self.items[3].values[i]))
                return

            if direction == DIRECTIONS.UP:
                play_sound('resources/sounds/woosh.wav')
                self.direction_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                i = self.index - 1 if self.index else len(self.items) - 1
                self.index = i
                return

            if direction == DIRECTIONS.DOWN:
                play_sound('resources/sounds/woosh.wav')
                self.direction_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                i = self.index + 1 if self.index < len(self.items) - 1 else 0
                self.index = i
                return

    def update_display_mode(self):
        mode = self.items[1].enum_index  # 0 FS, 1 Scaled, 2 windowed
        set_screen_display_mode(mode)


CONTROLLS_IMAGES = {
    'french': 'resources/ui/controls_fr.png',
    'english': 'resources/ui/controls_en.png'
}


class HowToPlayScreen:
    def __init__(self, joysticks):
        self.page = 0
        self.done = False
        self.joysticks = joysticks
        self.page_cooldown = 0
        self.button = NavigationButton('back_to_menu', 'B')

    @property
    def image(self):
        return get_how_to_play_image(self.page)

    def __next__(self):
        for joystick in self.joysticks:
            commands = get_current_commands(joystick)
            if commands.get('B'):
                self.done = True
                return
            if self.page_cooldown > 0:
                self.page_cooldown = max((self.page_cooldown - 1, 0))
            else:
                direction = get_pressed_direction(joystick)
                lr = direction in [DIRECTIONS.LEFT, DIRECTIONS.RIGHT]
                if not lr:
                    return
                play_sound('resources/sounds/coltclick.wav')
                if direction == DIRECTIONS.RIGHT:
                    self.page_cooldown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                    self.page = min((self.page + 1, 5))
                elif direction == DIRECTIONS.LEFT:
                    self.page_cooldown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                    self.page = max((self.page - 1, 0))


class ControlMenuScreen:
    def __init__(self, joysticks):
        image = CONTROLLS_IMAGES[preferences.get('language')]
        self.image = load_image(image)
        self.done = False
        self.joysticks = joysticks
        self.button = NavigationButton('back_to_menu', 'B')

    def __next__(self):
        for joystick in self.joysticks:
            commands = get_current_commands(joystick)
            if commands.get('B'):
                self.done = True


class bidirection_cycle:
    def __init__(self, iterable):
        self.index = 0
        self.iterable = iterable

    def __next__(self):
        self.index += 1
        if self.index >= len(self.iterable):
            self.index = 0
        return self.iterable[self.index]

    def next(self):
        return self.__next__()

    def previous(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.iterable) - 1
        return self.iterable[self.index]


class FinalScoreScreen:
    def __init__(self, players, scores, joysticks):
        self.joysticks = joysticks
        self.is_done = False
        self.players = players
        self.scores = scores
        self.background = load_image('resources/ui/scores/score_ul.png')
        self.winner_index = get_final_winner_index(scores)
        self.winner_animation = Winner(self.winner_index)
        score = scores[f'player {self.winner_index + 1}']
        self.winner_message = build_winner_message(score)
        self.player_message_keys = self.get_select_players_message_keys()
        self.button = NavigationButton('back_to_menu', 'A')
        self.cooldown = COUNTDOWNS.MENU_SELECTION_COOLDOWN

    def get_select_players_message_keys(self):
        most_sheet_keys = get_most_sheet(self.scores)
        already_assigned = []
        keys = []
        for most_keys in most_sheet_keys:
            most_keys = [k for k in most_keys if k not in already_assigned]
            if not most_keys:
                keys.append('boring')
                continue
            key = random.choice(most_keys)
            keys.append(key)
            already_assigned.append(key)
        return keys

    def __next__(self):
        next(self.winner_animation)

        if self.cooldown > 0:
            self.cooldown -= 1
            return

        for joystick in self.joysticks:
            commands = get_current_commands(joystick)
            if commands.get('A'):
                self.is_done = True


class ScoreSheetScreen:
    def __init__(self, players, winner_index, scores, joysticks):
        self.is_final = preferences.get('rounds') == scores['round']
        self.page = 0
        self.page_iterator = bidirection_cycle([0, 1])
        self.button_pages = 0
        self.scores = deepcopy(scores)
        self.joysticks = joysticks
        self.players = players
        self.winner_index = winner_index
        self.background = load_image('resources/ui/scores/score_ul.png')
        self.characters_coordinates = [
            Coordinates((85, 55)),
            Coordinates((230, 55)),
            Coordinates((367, 55)),
            Coordinates((506, 55))]
        self.columns = [
            (50, 168), (192, 310), (332, 450), (471, 592)]  # left and right
        self.round_left = 31
        self.lines = {
            'round': 21,
            'player': 94,
            'name': 134,
            'money': 161,
            'player_killed': (187, 201, 215),
            'npc_killed': 245,
            'victory': 267,
            'total': 302,
            'tot_wins': 133,
            'tot_death': 146,
            'tot_kills': (184, 198, 209),
            'tot_money': 251,
            'tot_npc_killed': 265,
            'tot_score': 305}
        self.page_cooldown = 0
        for player in self.players:
            animation = 'defeat' if player.index != winner_index else 'victory'
            player.character.spritesheet.animation = animation
            player.character.spritesheet.index = 0
        self.back_to_menu = False
        self.next_round = False
        self.done = True
        self._buttons = [
            NavigationButton('next_round', 'A'),
            NavigationButton('back_to_menu', 'B'),
            NavigationButton('yes', 'A'),
            NavigationButton('no', 'B'),
            NavigationButton('final_sheet', 'A')]

    @property
    def buttons(self):
        if self.is_final:
            return [self._buttons[4]]
        return (
            self._buttons[:2] if self.button_pages == 0
            else self._buttons[2:4])

    def show(self):
        self.page = 0
        self.next_round = False
        self.back_to_menu = False

    def __next__(self):
        for player in self.players:
            next(player.character)
        if self.page_cooldown > 0:
            self.page_cooldown = max((self.page_cooldown - 1, 0))
            return
        for joystick in self.joysticks:
            direction = get_pressed_direction(joystick)
            lr = direction in [DIRECTIONS.LEFT, DIRECTIONS.RIGHT]
            if lr and not self.page_cooldown:
                play_sound('resources/sounds/coltclick.wav')
                self.page_cooldown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                if direction == DIRECTIONS.LEFT:
                    self.page = self.page_iterator.previous()
                else:
                    self.page = next(self.page_iterator)
            commands = get_current_commands(joystick)
            if commands.get('B'):
                self.button_pages = 1 if self.button_pages == 0 else 0
                self.page_cooldown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                return
            if commands.get('A'):
                if self.button_pages == 0 or self.is_final:
                    self.next_round = True
                else:
                    self.back_to_menu = True
                return


class MenuItem:
    def __init__(self, index, label, coordinates):
        self.index = index
        self._label = label
        self.coordinates = Coordinates(coordinates)

    @property
    def label(self):
        return get_menu_text(self._label)


class EnumItem:
    def __init__(self, index, label, coordinates, values, default=None):
        self.index = index
        self._label = label
        self.coordinates = Coordinates(coordinates)
        self.values = values
        self.enum_index = 0 if not default else self.values.index(default)

    @property
    def label(self):
        value = self.values[self.enum_index]
        return f'{get_menu_text(self._label)}: <{get_menu_text(value)}>'

    def set_next(self, previous=False):
        if previous:
            length = len(self.values)
            i = self.enum_index - 1 if self.enum_index else length - 1
            self.enum_index = i
            return

        self.enum_index += 1
        try:
            self.values[self.enum_index]
        except IndexError:
            self.enum_index = 0


class Winner:
    def __init__(self, player_index):
        filepath = f'resources/animdata/p{player_index + 1}-win-animation.json'
        data = load_data(filepath)
        self.spritesheet = SpriteSheet(data, start_animation='loop')
        self.coordinates = Coordinates((235, 128))

    @property
    def image(self):
        return self.spritesheet.image()

    @property
    def render_position(self):
        return self.coordinates.position

    def __next__(self):
        if self.spritesheet.animation_is_done:
            self.spritesheet.index = 0
            return
        return next(self.spritesheet)


class Title:
    def __init__(self):
        data = load_data('resources/animdata/title.json')
        self.spritesheet = SpriteSheet(data, start_animation='waiting')
        self.loop_cooldown = COUNTDOWNS.TITLE_LOOP_COOLDOWN_MIN
        self.coordinates = Coordinates((0, 0))

    @property
    def image(self):
        return self.spritesheet.image()

    @property
    def render_position(self):
        return 0, 0

    @property
    def switch(self):
        return 1000000

    def __next__(self):
        if not self.spritesheet.animation_is_done:
            return next(self.spritesheet)

        if self.spritesheet.animation == 'waiting':
            self.spritesheet.animation = 'splash'
            self.spritesheet.index = 0
            return

        if self.spritesheet.animation == 'splash':
            self.spritesheet.animation = 'fix'
            self.spritesheet.index = 0
            return

        if self.spritesheet.animation == 'fix':
            if self.loop_cooldown:
                self.loop_cooldown -= 1
                return
            self.spritesheet.animation = 'loop'
            self.spritesheet.index = 0
            return

        if self.spritesheet.animation == 'loop':
            self.spritesheet.animation = 'fix'
            self.spritesheet.index = 0
            self.loop_cooldown = random.choice(range(
                COUNTDOWNS.TITLE_LOOP_COOLDOWN_MIN,
                COUNTDOWNS.TITLE_LOOP_COOLDOWN_MAX))


class NavigationButton:
    def __init__(self, text_key, button):
        self.image = get_touch_button_image(button)
        self.key = text_key


class PauseMenu:
    def __init__(self, joysticks):
        self.joysticks = joysticks
        self.button_countdown = 0
        self.index = 0
        self.buttons_visible = False
        self.done = False
        self.back_to_menu = False
        self.quit_game = False
        self.bg = load_image('resources/ui/pause-ul.png')
        self.items = [
            MenuItem(0, 'continue', (80, 210)),
            MenuItem(1, 'back_to_menu', (80, 228)),
            MenuItem(2, 'back_to_desktop', (80, 246))]
        self._buttons = [
            NavigationButton('yes', 'A'),
            NavigationButton('no', 'B')]

    @property
    def buttons(self):
        return self._buttons if self.buttons_visible else []

    def __next__(self):
        if self.button_countdown > 0:
            self.button_countdown -= 1
            return

        for joystick in self.joysticks:
            commands = get_current_commands(joystick)
            if commands.get('B'):
                self.buttons_visible = False
                self.button_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                return

            if commands.get('A'):
                if self.index == 0:
                    self.done = True
                    return
                if not self.buttons_visible:
                    self.buttons_visible = True
                    self.button_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                    return
                elif self.index == 1:
                    self.back_to_menu = True
                    return
                elif self.index == 2:
                    self.quit_game = True
                    return

            if self.buttons_visible:
                continue

            direction = get_pressed_direction(joystick)
            if direction == DIRECTIONS.UP:
                play_sound('resources/sounds/woosh.wav')
                self.button_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                i = self.index - 1 if self.index else len(self.items) - 1
                self.index = i
                return

            if direction == DIRECTIONS.DOWN:
                play_sound('resources/sounds/woosh.wav')
                self.button_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                i = self.index + 1 if self.index < len(self.items) - 1 else 0
                self.index = i
                return
