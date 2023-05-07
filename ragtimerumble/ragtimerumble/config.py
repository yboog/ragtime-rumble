import os

GAMEROOT = os.path.dirname(os.path.dirname(__file__))

AVAILABLE_LANGUAGES = ['english', 'french']
DEFAULT_SCENE = 'resources/scenes/saloon.json'
DOG_GROWL_DISTANCE = 70
DOG_BARK_DISTANCE = 40
GAMETYPES = ['advanced', 'basic']
DEAD_ANIMATIONS = ['death', 'coma']
LOOPING_ANIMATIONS = [
    'idle', 'walk', 'piano', 'poker',
    'suspicious', 'balcony', 'victory', 'defeat']
HOLDABLE_ANIMATIONS = ['call', 'death', 'coma']
SMOOTH_PATH_SELECTION_RADIUS = 50
HARD_PATH_SELECTION_RADIUS = 25
SMOOTH_PATH_USAGE_PROBABILITY = 7
HARD_PATH_USAGE_PROBABILITY = 10
MAX_MESSAGES = 3
PALLETTES_COUNT = 40
WIN_OR_LOOSE_AT_POKER_PROBABILITY = (3, 2)
RESOLUTION = 640, 360


class DISPLAY_MODES:
    FULSCREEN = 0
    SCALED = 1
    WINDOWED = 2


class DUEL:
    RANGE = (20, 120)
    TOLERENCE = 15


class LOOP_STATUSES:
    PAUSE = 'pause'
    AWAITING = 'awaiting'
    DISPATCHING = 'assignation'
    MENU = 'menu'
    BATTLE = 'fight'
    LAST_KILL = 'lastkill'
    SCORE = 'score'


class COUNTDOWNS:
    ACTION_COOLDOWN = 15
    BARMAN_IDLE_COOLDOWN_RANGE = (50, 150)
    BARMAN_WALK_COOLDOWN_RANGE = (25, 75)
    BOTTLE_ADD = 6000 // 3
    BULLET_COOLDOWN = 600
    BLACK_SCREEN = 92
    COMA_MIN = 500
    COMA_MAX = 10000
    COOLDOWN_MIN = 50
    COOLDOWN_MAX = 300
    COOLDOWN_PROBABILITY = 1
    DOG_IDLE_COOLDOWN_RANGE = (100, 300)
    DOG_WALK_COOLDOWN_RANGE = (20, 100)
    DUEL_CHECK_MIN = 300
    DUEL_CHECK_MAX = 800
    DUEL_RELEASE_TIME_MIN = 10
    DUEL_RELEASE_TIME_MAX = 95
    INTERACTION_PROBABILITY = 4
    INTERACTION_COOLDOWN_MIN = 125
    INTERACTION_COOLDOWN_MAX = 350
    INTERACTION_LOOP_COOLDOWN_MIN = 125
    INTERACTION_LOOP_COOLDOWN_MAX = 400
    MAX_LIFE = 6000
    MENU_SELECTION_COOLDOWN = 20
    MESSAGE_DISPLAY_TIME = 200
    MESSAGE_FADEOFF_EXPOSURE = 35
    POKER_BET_TIME_COOLDOWN = 240
    START_LIFE = 4499
    SNIPER_BULLET_COOLDOWN = 60
    TITLE_LOOP_COOLDOWN_MIN = 90
    TITLE_LOOP_COOLDOWN_MAX = 200
    VOMIT_MIN = 1000
    VOMIT_MAX = 5000
    WHITE_SCREEN = 8


class SPEED:
    BARMAN = 0.6
    DOG = .8
    FACTOR = 1.2
    MAX = 1.1
    MIN = .2
    SNIPER_RECTICLE_MIN = .2
    SNIPER_RECTICLE_MAX = 2.5
    SNIPER_RECTICLE_FACTOR = 1.15


class ELEMENT_TYPES:
    CHARACTER = 'character'
    PROP = 'prop'


class CHARACTER_STATUSES:
    AUTOPILOT = 'autopilot'
    DUEL_ORIGIN = 'duel_origin'
    DUEL_TARGET = 'duel_target'
    INTERACTING = 'interacting'
    OUT = 'out'
    FREE = 'free'
    STUCK = 'stuck'
    DUELABLES = [FREE, AUTOPILOT, STUCK]


class ANIMATION_SIDES:
    FACE = 'face'
    BACK = 'back'


class DIRECTIONS:
    NO = None

    LEFT = 'left'
    RIGHT = 'right'
    UP = 'up'
    DOWN = 'down'
    UP_LEFT = 'up_left'
    DOWN_LEFT = 'down_left'
    UP_RIGHT = 'up_right'
    DOWN_RIGHT = 'down_right'

    ALL = LEFT, RIGHT, UP, DOWN, UP_LEFT, DOWN_LEFT, UP_RIGHT, DOWN_RIGHT
    RIGHTS = RIGHT, UP_RIGHT, DOWN_RIGHT, UP, DOWN
    LEFTS = LEFT, UP_LEFT, DOWN_LEFT
    DIAGONALS = DOWN_LEFT, DOWN_RIGHT, UP_LEFT, UP_RIGHT
    FLIPPED = LEFTS


DIRECTION_TO_SIDE = {
    DIRECTIONS.RIGHT: ANIMATION_SIDES.FACE,
    DIRECTIONS.LEFT: ANIMATION_SIDES.FACE,
    DIRECTIONS.UP: ANIMATION_SIDES.BACK,
    DIRECTIONS.DOWN: ANIMATION_SIDES.FACE,
    DIRECTIONS.DOWN_RIGHT: ANIMATION_SIDES.FACE,
    DIRECTIONS.UP_RIGHT: ANIMATION_SIDES.BACK,
    DIRECTIONS.DOWN_LEFT: ANIMATION_SIDES.FACE,
    DIRECTIONS.UP_LEFT: ANIMATION_SIDES.BACK,
}


HAT_TO_DIRECTION = {
    (1, 0): DIRECTIONS.RIGHT,
    (-1, 0): DIRECTIONS.LEFT,
    (0, -1): DIRECTIONS.UP,
    (0, 1): DIRECTIONS.DOWN,
    (1, 1): DIRECTIONS.DOWN_RIGHT,
    (1, -1): DIRECTIONS.UP_RIGHT,
    (-1, 1): DIRECTIONS.DOWN_LEFT,
    (-1, -1): DIRECTIONS.UP_LEFT
}


DIRECTION_TO_VECTOR = {v: k for k, v in HAT_TO_DIRECTION.items()}
