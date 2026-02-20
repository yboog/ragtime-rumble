import os
import subprocess

here = os.path.dirname(__file__)
engine_folder = f'{here}/ragtimerumble'
env = {'PYTHONPATH': engine_folder}
os.environ.update(env)
subprocess.call(
    ['py', '-3.12', f'{engine_folder}/ragtimerumble'], env=os.environ)