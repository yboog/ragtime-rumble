
import pygame
from ragtimerumble.config import RESOLUTION, DISPLAY_MODES
from ragtimerumble.io import get_icon


_screen = None


def get_screen():
    return _screen


def set_screen_display_mode(display_mode):
    global _screen
    match display_mode:
        case DISPLAY_MODES.FULLSCREEN:
            _screen = pygame.display.set_mode(
                RESOLUTION, pygame.SCALED | pygame.FULLSCREEN)
        case DISPLAY_MODES.SCALED:
            _screen = pygame.display.set_mode(RESOLUTION, pygame.SCALED)
        case DISPLAY_MODES.WINDOWED:
            _screen = pygame.display.set_mode(RESOLUTION)
    pygame.display.set_caption('Ragtime Rumble')
    pygame.display.set_icon(get_icon())
