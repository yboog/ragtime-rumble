from ragtimerumble import preferences
from ragtimerumble.config import (
    GAMEROOT, COUNTDOWNS, DIRECTIONS, AVAILABLE_LANGUAGES)
from ragtimerumble.display import set_screen_display_mode
from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data, load_image, get_menu_text
from ragtimerumble.sprite import SpriteSheet
from ragtimerumble.joystick import get_pressed_direction, get_current_commands


class Menu:
    def __init__(self, joysticks):
        self.title = Title()
        self.joysticks = joysticks
        self.index = 0
        self.bg = load_image('resources/ui/title-bg.png')
        self.done = False
        self.start = False
        displays = ('fullscreen', 'wscaled', 'windowed')
        self.items = [
            EnumItem(0, 'new_game', (361, 185), values=('advanced', 'basic')),
            EnumItem(1, 'display', (361, 210), values=displays),
            EnumItem(2, 'language', (361, 225), values=AVAILABLE_LANGUAGES),
            MenuItem(3, 'controls', (361, 250)),
            MenuItem(4, 'help', (361, 265)),
            MenuItem(5, 'quit', (361, 290))]
        self.direction_countdown = 0

    def __next__(self):
        next(self.title)
        for joystick in self.joysticks:
            commands = get_current_commands(joystick)
            if commands.get('A'):
                if self.index == 5:
                    self.done = True
                    return
                if self.index == 0:
                    self.start = True

            if self.direction_countdown > 0:
                self.direction_countdown -= 1
                continue

            direction = get_pressed_direction(joystick)
            directions = (DIRECTIONS.LEFT, DIRECTIONS.RIGHT)
            enums = 0, 1, 2
            if direction in directions and self.index in enums:
                self.items[self.index].set_next(direction == DIRECTIONS.LEFT)
                self.direction_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                if self.index == 1:
                    self.update_display_mode()
                if self.index == 2:
                    i = self.items[2].enum_index
                    preferences.set('language', AVAILABLE_LANGUAGES[i])
                return

            if direction == DIRECTIONS.UP:
                self.direction_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                i = self.index - 1 if self.index else len(self.items) - 1
                self.index = i
                return

            if direction == DIRECTIONS.DOWN:
                self.direction_countdown = COUNTDOWNS.MENU_SELECTION_COOLDOWN
                i = self.index + 1 if self.index < len(self.items) - 1 else 0
                self.index = i
                return

    def update_display_mode(self):
        mode = self.items[1].enum_index  # 0 FS, 1 Scaled, 2 windowed
        set_screen_display_mode(mode)


class MenuItem:
    def __init__(self, index, label, coordinates):
        self.index = index
        self._label = label
        self.coordinates = Coordinates(coordinates)

    @property
    def label(self):
        return get_menu_text(self._label)


class EnumItem:
    def __init__(self, index, label, coordinates, values):
        self.index = index
        self._label = label
        self.coordinates = Coordinates(coordinates)
        self.values = values
        self.enum_index = 0

    @property
    def label(self):
        value = self.values[self.enum_index]
        return f'{get_menu_text(self._label)}: <{get_menu_text(value)}>'

    def set_next(self, previous=False):
        if previous:
            i = self.enum_index - 1 if self.enum_index else len(self.values) - 1
            self.enum_index = i
            return

        self.enum_index += 1
        try:
            self.values[self.enum_index]
        except IndexError:
            self.enum_index = 0


class Title:
    def __init__(self):
        data = load_data('resources/animdata/title.json')
        self.spritesheet = SpriteSheet(data, start_animation='waiting')
        self.loop_cooldown = COUNTDOWNS.TITLE_LOOP_COOLDOWN
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
            self.loop_cooldown = COUNTDOWNS.TITLE_LOOP_COOLDOWN
