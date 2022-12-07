import os
import subprocess

here = os.path.dirname(__file__)
engine_folder = f'{here}/drunkparanoia'
env = {'PYTHONPATH': engine_folder}
os.environ.update(env)
subprocess.call(['py', '-3.10', f'{engine_folder}/drunkparanoia'], env=os.environ)