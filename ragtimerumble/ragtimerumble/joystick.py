from ragtimerumble.config import DIRECTIONS


def get_keystate(key_name, joystick):
    name_to_function = {
        'XBox One S Controller': get_x_input_keystate,
        'Controller (8BitDo Pro 2)': get_x_input_keystate,
        'USB,2-axis 8-button gamepad': get_2_axis_8_button_keystate,
        'Generic USB Joystick': get_generic_user_joystick_keystate,
        'PS4 Controller': get_ps4_controller_keystate
    }
    function = name_to_function.get(joystick.get_name(), get_x_input_keystate)
    return function(key_name, joystick)


def get_2_axis_8_button_keystate(key_name, joystick):
    match key_name:
        case "A":
            return joystick.get_button(1) == 1
        case 'X':
            return joystick.get_button(3) == 1
        case 'select':
            return joystick.get_button(6) == 1
        case 'start':
            return joystick.get_button(7) == 1
        case 'UP':
            return joystick.get_axis(1) < -.5
        case 'DOWN':
            return joystick.get_axis(1) > .5
        case 'LEFT':
            return joystick.get_axis(0) < -.5
        case 'RIGHT':
            return joystick.get_axis(0) > .5
    return False


def get_ps4_controller_keystate(key_name, joystick):
    match key_name:
        case "A":
            return joystick.get_button(0) == 1
        case 'X':
            return joystick.get_button(2) == 1
        case 'Y':
            return joystick.get_button(3) == 1
        case 'B':
            return joystick.get_button(1) == 1
        case 'select':
            return joystick.get_button(4) == 1
        case 'start':
            return joystick.get_button(6) == 1
        case 'UP':
            return joystick.get_button(11) == 1 or joystick.get_axis(1) < -.5
        case 'DOWN':
            return joystick.get_button(12) == 1 or joystick.get_axis(1) > .5
        case 'LEFT':
            return joystick.get_button(13) == 1 or joystick.get_axis(0) < -.5
        case 'RIGHT':
            return joystick.get_button(14) == 1 or joystick.get_axis(0) > .5
        case 'RS_LEFT':
            return joystick.get_axis(2) < -.5
        case 'RS_RIGHT':
            return joystick.get_axis(2) > .5
        case 'RS_UP':
            return joystick.get_axis(4) < -.5
        case 'RS_DOWN':
            return joystick.get_axis(4) > .5
    return False


def get_generic_user_joystick_keystate(key_name, joystick):
    match key_name:
        case "A":
            return joystick.get_button(2) == 1
        case 'X':
            return joystick.get_button(3) == 1
        case 'Y':
            return joystick.get_button(0) == 1
        case 'select':
            return joystick.get_button(6) == 1
        case 'start':
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
        case 'RS_UP':
            return joystick.get_axis(4) < -.5
        case 'RS_DOWN':
            return joystick.get_axis(4) > .5
    return False


def get_x_input_keystate(key_name, joystick):
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
        case 'RS_UP':
            return joystick.get_axis(3) < -.5
        case 'RS_DOWN':
            return joystick.get_axis(3) > .5
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
        'RS_RIGHT': get_keystate('RS_RIGHT', joystick),
        'RS_UP': get_keystate('RS_UP', joystick),
        'RS_DOWN': get_keystate('RS_DOWN', joystick)
    }


def get_pressed_direction(joystick, rs=False):
    left = get_keystate('RS_LEFT' if rs else 'LEFT', joystick)
    right = get_keystate('RS_RIGHT' if rs else 'RIGHT', joystick)
    up = get_keystate('RS_UP' if rs else 'UP', joystick)
    down = get_keystate('RS_DOWN' if rs else 'DOWN', joystick)
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
