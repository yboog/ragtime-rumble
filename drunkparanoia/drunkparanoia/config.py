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
    'troughout',
    'coma'
]
LOOPING_ANIMATIONS = ['idle', 'walk', 'piano', 'poker', 'pee_in_pant']


class CHARACTER_STATES:
    STUCK = 'stuck'
    MOVING = 'moving'
    IDLE = 'idle'
    INTERACTING = 'interacting'


class ANIMATION_SIDES:
    SIDE = 'side'
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


DIRECTION_TO_SIDE = {
    DIRECTIONS.RIGHT: ANIMATION_SIDES.SIDE,
    DIRECTIONS.LEFT: ANIMATION_SIDES.SIDE,
    DIRECTIONS.UP: ANIMATION_SIDES.BACK,
    DIRECTIONS.DOWN: ANIMATION_SIDES.FACE,
    DIRECTIONS.DOWN_RIGHT: ANIMATION_SIDES.SIDE,
    DIRECTIONS.UP_RIGHT: ANIMATION_SIDES.SIDE,
    DIRECTIONS.DOWN_LEFT: ANIMATION_SIDES.SIDE,
    DIRECTIONS.UP_LEFT: ANIMATION_SIDES.SIDE,
}


FLIPPED_DIRECTIONS = [
    DIRECTIONS.LEFT,
    DIRECTIONS.UP_LEFT,
    DIRECTIONS.DOWN_LEFT
]


HAT_TO_DIRECTIONS = {
    (1, 0): DIRECTIONS.RIGHT,
    (-1, 0): DIRECTIONS.LEFT,
    (0, -1): DIRECTIONS.UP,
    (0, 1): DIRECTIONS.DOWN,
    (1, 1): DIRECTIONS.DOWN_RIGHT,
    (1, -1): DIRECTIONS.UP_RIGHT,
    (-1, 1): DIRECTIONS.DOWN_LEFT,
    (-1, -1): DIRECTIONS.UP_LEFT
}


DIAGONALS = [
    DIRECTIONS.DOWN_LEFT,
    DIRECTIONS.DOWN_RIGHT,
    DIRECTIONS.UP_LEFT,
    DIRECTIONS.UP_RIGHT
]

DIRECTION_TO_VECTOR = {v: k for k, v in HAT_TO_DIRECTIONS.items()}