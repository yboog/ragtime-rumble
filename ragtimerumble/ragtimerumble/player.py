
import random
from ragtimerumble.joystick import get_pressed_direction, get_current_commands
from ragtimerumble.config import (
    LOOPING_ANIMATIONS, CHARACTER_STATUSES, COUNTDOWNS,
    WIN_OR_LOOSE_AT_POKER_PROBABILITY)
from ragtimerumble.io import (
    play_sound, choice_death_sentence, choice_random_name, play_coin_sound)


class Player:

    def __init__(self, character, joystick, index, scene):
        self.character = character
        self.scene = scene
        self.joystick = joystick
        self.life = COUNTDOWNS.MAX_LIFE
        self.bullet_cooldown = 0
        self.action_cooldown = 0
        self._coins = 1
        self.index = index
        self.killer = None
        self.npc_killed = 0
        self.poker_iterator = PokerIterator(self)

    @property
    def coins(self):
        return self._coins

    @coins.setter
    def coins(self, n):
        self._coins = min((n, max((0, 5))))

    @property
    def dying(self):
        return (
            self.character.status == CHARACTER_STATUSES.OUT and
            not self.character.spritesheet.animation_is_done)

    def fall_to_coma(self):
        if self.character.status == CHARACTER_STATUSES.OUT:
            next(self.character)
            return

        if self.character.duel_target:
            self.release_target()

        self.character.status = CHARACTER_STATUSES.OUT
        self.character.spritesheet.animation = 'vomit'
        self.character.spritesheet.index = 0
        self.character.buffer_animation = 'coma'
        player = self.scene.find_player(self)
        name = (
            f'Player {player.index + 1}'
            if player else choice_random_name(self.character.gender))
        messenger = self.scene.messenger
        sentence = choice_death_sentence('french')
        messenger.add_message(sentence.format(name=name))
        return

    def release_target(self):
        target = self.character.duel_target
        target.duel_target = None
        target.spritesheet.animation = 'idle'
        target.spritesheet.index = 0
        target.status = (
            CHARACTER_STATUSES.AUTOPILOT if target.pilot else
            CHARACTER_STATUSES.FREE)
        self.character.duel_target = None

    @property
    def dead(self):
        return (
            self.character.status == CHARACTER_STATUSES.OUT and
            self.character.spritesheet.animation_is_done)

    def kill(self, target, black_screen=False, silently=False):
        self.character.kill(target, black_screen, silently)
        player = self.scene.find_player(target)
        if player:
            player.killer = self.index
            player.life = 0
        else:
            self.npc_killed += 1
        self.bullet_cooldown = COUNTDOWNS.BULLET_COOLDOWN

    def __next__(self):

        if self.character.status == CHARACTER_STATUSES.OUT:
            next(self.character)
            return

        self.life -= 1
        if self.life == 0:
            return self.fall_to_coma()

        commands = get_current_commands(self.joystick)
        if commands.get('X'):
            for sniper in self.scene.snipers:
                if sniper.reticle.player == self:
                    self.bullet_cooldown = 60
                    return sniper.shoot()

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
        if self.character.spritesheet.animation_is_done:
            if self.character.spritesheet.animation == 'order':
                if self.coins:
                    position = self.character.coordinates.position[:]
                    self.scene.create_interactive_prop(position, 'bottle')
                    self.coins -= 1
                self.character.set_free()
            elif self.character.spritesheet.animation == 'drink':
                life = self.life + COUNTDOWNS.BOTTLE_ADD
                self.life = min((COUNTDOWNS.MAX_LIFE, life))
                self.character.set_free()
                return

        is_looping = self.character.spritesheet.animation in LOOPING_ANIMATIONS
        commands = get_current_commands(self.joystick)
        if not is_looping or not commands.get('Y') or self.action_cooldown:
            if self.character.spritesheet.animation == 'poker':
                next(self.poker_iterator)
            next(self.character)
            return

        self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN
        self.character.set_free()

    def evaluate_duel_as_target(self):
        commands = get_current_commands(self.joystick)
        if not self.character.duel_target:
            return
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
            character = self.character.request_stripping()
            if character is not None and self.coins < 5:
                play_coin_sound()
                character.shorn = True
                self.coins += 1
                self.create_coin_vfx()
                self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN
                return True
            if self.action_cooldown != 0:
                return False
            interact = self.check_snipers()
            interact = interact or self.character.request_interaction()
            if interact:
                self.action_cooldown = COUNTDOWNS.ACTION_COOLDOWN
                return True
        return False

    def create_coin_vfx(self):
        position = list(self.character.coordinates.position)
        position[1] -= 10
        position[1] -= 50
        self.scene.create_vfx('coin-alert', position)

    def check_snipers(self):
        return next((
            sniper.corruption_attempt(self)
            for sniper in self.scene.snipers
            if sniper.meet(self.character.coordinates.position)),
            False)


class PokerIterator:

    def __init__(self, player):
        self.player = player
        self.cooldown = COUNTDOWNS.POKER_BET_TIME_COOLDOWN

    def __next__(self):
        if self.cooldown > 0:
            self.cooldown -= 1
            return

        self.cooldown = COUNTDOWNS.POKER_BET_TIME_COOLDOWN
        if self.player.coins:
            self.bet()
        return

    def bet(self):
        win, loose = WIN_OR_LOOSE_AT_POKER_PROBABILITY
        victory = random.choice([True] * win + [False] * loose)
        self.player.coins += 1 if victory else -1