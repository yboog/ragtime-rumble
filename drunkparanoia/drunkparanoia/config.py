import os

GAMEROOT = os.path.dirname(os.path.dirname(__file__))

ANIMATIONS = [
    'idle',
    'walk',
    'order',
    'drink',
    'piano',
    'poker',
    'bully',
    'pee_in_pant',
    'bet',
    'call',
    'smoke',
    'bloodydeath',
    'vomit',
    'coma'
]
LOOPING_ANIMATIONS = ['idle', 'walk', 'piano', 'poker', 'suspicious']
HOLDABLE_ANIMATIONS = ['call', 'death', 'coma']


class LOOP_STATUSES:
    PAUSE = 'pause'
    AWAITING = 'awaiting'
    DISPATCHING = 'assignation'
    BATTLE = 'fight'
    LAST_KILL = 'lastkill'
    SCORE = 'score'


class COUNTDOWNS:
    VOMIT_MIN = 1000
    VOMIT_MAX = 1800
    COMA_MIN = 500
    COMA_MAX = 10000
    COOLDOWN_MIN = 50
    COOLDOWN_MAX = 300
    COOLDOWN_PROBABILITY = 2
    DUEL_CHECK_MIN = 50
    DUEL_CHECK_MAX = 250
    DUEL_RELEASE_TIME_MIN = 10
    DUEL_RELEASE_TIME_MAX = 125
    BLACK_SCREEN = 92
    WHITE_SCREEN = 8
    START_LIFE = 1500
    MAX_LIFE = 2000


class SPEED:
    MAX = 1.25
    MIN = .2
    FACTOR = 1.2


class ELEMENT_TYPES:
    CHARACTER = 'character'
    PROP = 'prop'


class CHARACTER_STATUSES:
    DUEL_ORIGIN = 'duel_origin'
    DUEL_TARGET = 'duel_target'
    INTERACTING = 'interacting'
    AUTOPILOT = 'autopilot'
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
    RIGHTS = RIGHT, UP_RIGHT, DOWN_RIGHT
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