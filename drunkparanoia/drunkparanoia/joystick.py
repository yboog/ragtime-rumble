from drunkparanoia.config import DIRECTIONS


def get_keystate(key_name, joystick):
    match key_name:
        case "A":
            return joystick.get_button(0) == 1
        case 'B':
            return joystick.get_button(1) == 1
        case 'X':
            return joystick.get_button(2) == 1
        case 'Y':
            return joystick.get_button(3) == 1
        case 'L1':
            return joystick.get_button(4) == 1
        case 'L2':
            return joystick.get_axis(4) > .5
        case 'R1':
            return joystick.get_button(5) == 1
        case 'R2':
            return joystick.get_axis(5) > .5
        case 'select':
            return joystick.get_button(6) == 1
        case 'start':
            return joystick.get_button(7) == 1
        case 'LSB':
            return joystick.get_button(8) == 1
        case 'RSB':
            return joystick.get_button(9) == 1
        case 'UP':
            return joystick.get_hat(0)[1] == 1 or joystick.get_axis(1) < -.5
        case 'DOWN':
            return joystick.get_hat(0)[1] == -1 or joystick.get_axis(1) > .5
        case 'LEFT':
            return joystick.get_hat(0)[0] == -1 or joystick.get_axis(0) < -.5
        case 'RIGHT':
            return joystick.get_hat(0)[0] == 1 or joystick.get_axis(0) > .5
        case 'RS_LEFT':
            return joystick.get_axis(2) < -.5
        case 'RS_RIGHT':
            return joystick.get_axis(2) > .5
    raise KeyError(f'Unknown key {key_name}')


def get_current_commands(joystick):
    return {
        'A': get_keystate('A', joystick),
        'B': get_keystate('B', joystick),
        'X': get_keystate('X', joystick),
        'Y': get_keystate('Y', joystick),
        'L1': get_keystate('L1', joystick),
        'L2': get_keystate('L2', joystick),
        'R1': get_keystate('R1', joystick),
        'R2': get_keystate('R2', joystick),
        'select': get_keystate('select', joystick),
        'start': get_keystate('start', joystick),
        'LSB': get_keystate('LSB', joystick),
        'RSB': get_keystate('RSB', joystick),
        'UP': get_keystate('UP', joystick),
        'DOWN': get_keystate('DOWN', joystick),
        'LEFT': get_keystate('LEFT', joystick),
        'RIGHT': get_keystate('RIGHT', joystick),
        'RS_LEFT': get_keystate('RS_LEFT', joystick),
        'RS_RIGHT': get_keystate('RS_RIGHT', joystick)
    }


def get_pressed_direction(joystick):
    left = get_keystate('LEFT', joystick)
    right = get_keystate('RIGHT', joystick)
    up = get_keystate('UP', joystick)
    down = get_keystate('DOWN', joystick)
    if left and down:
        return DIRECTIONS.DOWN_LEFT
    elif left and up:
        return DIRECTIONS.UP_LEFT
    elif left:
        return DIRECTIONS.LEFT
    elif right and down:
        return DIRECTIONS.DOWN_RIGHT
    elif right and up:
        return DIRECTIONS.UP_RIGHT
    elif right:
        return DIRECTIONS.RIGHT
    elif up:
        return DIRECTIONS.UP
    elif down:
        return DIRECTIONS.DOWN
    return DIRECTIONS.NO