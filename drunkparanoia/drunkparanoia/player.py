
from drunkparanoia.joystick import get_pressed_direction, get_current_commands
from drunkparanoia.config import (
    LOOPING_ANIMATIONS, CHARACTER_STATUSES, COUNTDOWNS)
from drunkparanoia.io import play_sound


class Player:

    def __init__(self, character, joystick, index, scene):
        self.character = character
        self.scene = scene
        self.joystick = joystick
        self.life = COUNTDOWNS.MAX_LIFE
        self.bullet_cooldown = 0
        self.action_cooldown = 0
        self.index = index
        self.killer = None
        self.npc_killed = 0

    @property
    def dying(self):
        return (
            self.character.status == CHARACTER_STATUSES.OUT and
            not self.character.spritesheet.animation_is_done)

    @property
    def dead(self):
        return (
            self.character.status == CHARACTER_STATUSES.OUT and
            self.character.spritesheet.animation_is_done)

    def kill(self, target, black_screen=False):
        self.character.kill(target, black_screen)
        player = self.scene.find_player(target)
        if player:
            player.killer = self.index
            player.life = 0
        else:
            self.npc_killed += 1
        self.bullet_cooldown = COUNTDOWNS.BULLET_COOLDOWN

    def __next__(self):
        # self.life -= 1
        if self.character.status == CHARACTER_STATUSES.OUT:
            next(self.character)
            return

        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

        if self.bullet_cooldown == 1:
            play_sound('resources/sounds/coltclick.wav')

        if self.action_cooldown > 0:
            self.action_cooldown -= 1

        match self.character.status:
            case CHARACTER_STATUSES.STUCK:
                next(self.character)
                return

            case CHARACTER_STATUSES.FREE:
                if self.evaluate_free():
                    return

            case CHARACTER_STATUSES.DUEL_ORIGIN:
                return self.evaluate_duel_as_origin()

            case CHARACTER_STATUSES.DUEL_TARGET:
                return self.evaluate_duel_as_target()

            case CHARACTER_STATUSES.INTERACTING:
                return self.evaluate_interacting()

            case CHARACTER_STATUSES.AUTOPILOT:
                next(self.character)
                return

        direction = get_pressed_direction(self.joystick)
        if direction:
            self.character.direction = direction
            self.character.accelerate()
        else:
            self.character.decelerate()
        next(self.character)

    def evaluate_interacting(self):
        condition = (
            self.character.spritesheet.animation_is_done and
            self.character.spritesheet.animation == 'order')

        if condition:
            position = self.character.coordinates.position[:]
            self.scene.create_interactive_prop(position, 'bottle')
            self.character.set_free()
            return

        is_looping = self.character.spritesheet.animation in LOOPING_ANIMATIONS
        commands = get_current_commands(self.joystick)
        if not is_looping or not commands.get('Y') or self.action_cooldown:
            next(self.character)
            return

        self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN
        self.character.set_free()

    def evaluate_duel_as_target(self):
        commands = get_current_commands(self.joystick)
        if commands.get('X') and not self.bullet_cooldown:
            target = self.character.duel_target
            self.character.aim(target)
            self.kill(target, black_screen=True)
        if not self.character.spritesheet.animation_is_done:
            next(self.character)

    def evaluate_duel_as_origin(self):
        if not self.character.spritesheet.animation_is_done:
            next(self.character)
            return
        commands = get_current_commands(self.joystick)
        if commands.get('X') and not self.bullet_cooldown:
            self.kill(self.character.duel_target, black_screen=True)

        if commands.get('A'):
            self.character.release_duel()
        next(self.character)

    def evaluate_free(self):
        commands = get_current_commands(self.joystick)
        if commands.get('A'):
            self.character.stop()
            self.character.request_duel()
            return True

        if commands.get('X') and not self.bullet_cooldown:
            for character1, character2 in self.scene.possible_duels:
                if character1 == self.character:
                    self.kill(character2)
                    self.scene.apply_white_screen(self.character)
                    return True

        if commands.get('Y'):
            if self.action_cooldown != 0:
                return False
            interact = self.character.request_interaction()
            if interact:
                self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN
                return True

        return False
