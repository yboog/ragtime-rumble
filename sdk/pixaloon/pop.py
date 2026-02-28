import os
import subprocess
from pixaloon.path import relative_normpath


def get_command_root(gameroot):
    if os.path.exists(f'{gameroot}/ragtime.exe'):
        return [f'{gameroot}/ragtime.exe']
    if os.path.exists(f'{gameroot}/ragtimerumble'):
        return ['py', '-3.12', f'{gameroot}/ragtimerumble']
    raise ValueError(f'Document not in a valid game root: {gameroot}')


def run_game(
        document,
        windowed=True,
        record_replay_filepath=None,
        use_document_as_default_scene=True,
        loop_on_default_scene=True):
    if not document.filepath:
        raise ValueError('Document must be saved first')
    command = get_command_root(document.gameroot)
    if use_document_as_default_scene:
        path = relative_normpath(document.filepath, document)
        command.extend(('--default_scene', path))
    if loop_on_default_scene:
        command.append('--loop_on_default_scene')
    if record_replay_filepath is not None:
        command.extend(('--record_replay_filepath', record_replay_filepath))
        command.append('--unlocked_fps')
    if windowed:
        command.append('--windowed')
    subprocess.run(command)
