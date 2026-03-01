# Command to build: python setup.py build

from cx_Freeze import setup, Executable
import os
import json


HERE = os.path.dirname(__file__)

with open(f'{HERE}/build_config.json', 'r') as f:
    config = json.load(f)
print(f'Build: {config["executable"]}')

import pprint
print("CONFIG ---")
pprint.pprint(config)

executable = Executable(
    config["executable"],
    target_name='Ragtime-Rumble.exe',
    # base='Win32GUI',
    icon=config['icon'])

build_options = {
    'build_exe': config['name'],
    'includes': config['includes']}

setup(
    name="RagtimeRumble",
    version=config['version'],
    description="Ragtime Ready to Rumble",
    author="Jean-Loup Comby & Lionel Brouyère",
    options={"build_exe": build_options},
    executables=[executable],
)
