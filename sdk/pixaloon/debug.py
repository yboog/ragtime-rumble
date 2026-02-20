from colorama import Fore
import inspect


def print_stack():
    stack = inspect.stack()
    previous_filename = None
    message = ''
    for caller_frame in stack:
        fn = caller_frame.filename.replace('\\', '/')
        if fn.endswith('flyp/client.py'):
            continue
        func = caller_frame.function
        if fn.endswith('runpy.py'):
            break
        num = caller_frame.lineno
        if fn == previous_filename:
            message += f'{Fore.YELLOW}, {num}:{func}(){Fore.RESET}'
            previous_filename = fn
            continue
        previous_filename = fn
        message += (
            f'\n    {Fore.LIGHTBLACK_EX}{fn}: '
            f'{Fore.YELLOW}{num}:{func}(){Fore.RESET}')
    print(message)