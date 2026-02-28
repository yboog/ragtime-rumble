import sys
import pickle
import pygame

import os
sys.path.append(f'{os.path.dirname(__file__)}/..')

from ragtimerumble.io import load_skins, load_main_resources
from ragtimerumble.config import DISPLAY_MODES, LOOP_STATUSES
from ragtimerumble.display import set_screen_display_mode, get_screen
from ragtimerumble.gameloop import GameLoop
from ragtimerumble.render import render_game
from ragtimerumble import debug

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-ds', '--default_scene', type=str, default=None)
parser.add_argument('-lods', '--loop_on_default_scene', action='store_true', default=False)
parser.add_argument('-w', '--windowed', action='store_true', default=False)
parser.add_argument('-ufps', '--unlocked_fps', action='store_true', default=False)
parser.add_argument('-r', '--record_replay_filepath', type=str)

arguments = parser.parse_args()

pygame.init()
set_screen_display_mode(
    DISPLAY_MODES.SCALED if arguments.windowed else DISPLAY_MODES.FULLSCREEN)
pygame.joystick.init()
load_skins()
load_main_resources()
loop = GameLoop(
    unlocked_fps=arguments.unlocked_fps,
    default_scene=arguments.default_scene,
    loop_on_default_scene=arguments.loop_on_default_scene)

loop.set_scene(next(loop.scenes_iterator))

replay = []
while not loop.done:
    next(loop)
    if arguments.record_replay_filepath and loop.status == LOOP_STATUSES.BATTLE:
        try:
            positions = [
                (c.coordinates.position, c.status, c.pilot is None)
                for c in loop.scene.characters]
            replay.append(positions)
        except TypeError:
            positions = [c.coordinates.position for c in loop.scene.characters]
            exit()
    render_game(get_screen(), loop)
    pygame.display.update()
    if debug.log_coordinates:
        debug.log_npc_coordinates(loop.scene)

if replay:
    with open(arguments.record_replay_filepath, 'wb') as f:
        pickle.dump(replay, f)

debug.close()
sys.exit(0)
