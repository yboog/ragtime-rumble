# Command to build: python setup.py build

import sys
from cx_Freeze import setup, Executable
import os
import shutil
import py7zr
import yaml


desktop = os.path.expanduser("~/Desktop")
gameroot = os.path.join(desktop, "ragtimerumble")

if os.path.exists(gameroot):
    print(f'Build is already found at this directory {gameroot}')
    result = input('Would you like to erase it ? (y): ')
    if result != 'y':
        exit()
    shutil.rmtree(gameroot)


VERSION_YAML_FILE = f'{os.path.dirname(__file__)}/version.yaml'
with open(VERSION_YAML_FILE, 'r') as f:
    version_data = yaml.full_load(f)
    version_data['build'] += 1
    if '--minor' in sys.argv or '-m' in sys.argv:
        version_data['minor'] += 1
    elif '--major' in sys.argv or '-M' in sys.argv:
        version_data['major'] += 1
        version_data['minor'] = 0


with open(VERSION_YAML_FILE, 'w') as f:
    yaml.dump(version_data, f)

sys.argv = sys.argv[:2]  # Remove incompatible arguments with setup function.

build_exe_options = {
    "excludes": [
        "tkinter", "unittest", "email", "pkg_resources", "xml", "pydoc_data",
        "PySide6", "PyQt5", "PySide2", "PyQt6", "pyexpat", "ctypes", "pandas",
        "shiboken2", "sip", "sip2", "shiboken6", "sip6"]}


setup(
    name="Ragtime Rumble",
    author="Jean-Loup Comby & Lionel Brouyère",
    options={"build_exe": build_exe_options},
    executables=[Executable('ragtimerumble/__main__.py')])


current = os.path.dirname(__file__)
src = os.path.join(current, "build/exe.win-amd64-3.10")
os.makedirs(gameroot)
file_names = os.listdir(src)
for file_name in file_names:
    shutil.move(os.path.join(src, file_name), gameroot)

os.rename(
    f'{gameroot}/__main__.exe',
    f'{gameroot}/ragtime.exe')

shutil.copytree(
    src=f'{current}/resources',
    dst=f'{gameroot}/lib/resources')

version = (
    f'{version_data["major"]}.{version_data["minor"]}.'
    f'b{version_data["build"]}-{version_data["name"]}')
with open(f'{gameroot}/lib/resources/version', 'w') as f:
    f.write(version)


destination = f'{desktop}/ragtimerumble-{version}.7z'
with py7zr.SevenZipFile(destination, 'w') as archive:
    archive.writeall(gameroot, arcname=os.path.basename(gameroot))
