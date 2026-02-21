import os
import subprocess
import sys

here = os.path.dirname(__file__)
engine_folder = f'{here}/ragtimerumble'
env = {'PYTHONPATH': engine_folder}
os.environ.update(env)
subprocess.call(
    ['py', '-3.12', f'{engine_folder}/ragtimerumble', *sys.argv[1:]],
    env=os.environ)