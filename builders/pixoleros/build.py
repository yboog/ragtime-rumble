import os
import json
import yaml
import shutil
import argparse
import datetime
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--build_directory',
    help='Build Directory')

help_ = """\
Preserve venv created by the build.
This must be manually deleted before trigger another build."""
parser.add_argument(
    '-p', '--preserve_venv',
    action='store_true',
    default=False,
    help=help_)

help_ = """\
Major version build incrementation."""
parser.add_argument(
    '-M', '--major',
    action='store_true',
    default=False,
    help=help_)

help_ = """\
Minor version build incrementation."""
parser.add_argument(
    '-m', '--minor',
    action='store_true',
    default=False,
    help=help_)

parser.add_argument(
    '-z', '--create_archive',
    action='store_true',
    default=False,
    help='Package the build as an archive file.')


args = parser.parse_args()


# Setup build directory
if args.build_directory:
    ROOT = args.build_directory
    os.makedirs(ROOT, exist_ok=True)
    os.chdir(ROOT)
else:
    ROOT = os.getcwd()

print("ROOT", ROOT, args.build_directory)

venv_name = 'pixoleros_venv'
HERE = os.path.dirname(__file__)
PIXOLEROS_ROOT = f'{HERE}/../../sdk/pixoleros'

# Build venv and install/copy dependencies
requirement_paths = [f'{HERE}/requirements.txt']
ps1_script = f"""py -3.12 -m venv {venv_name}
{venv_name}/Scripts/activate
"""
for requirement_path in requirement_paths:
    ps1_script += f'pip install --index-url https://pypi.org/simple --no-cache-dir -r {requirement_path}\n'
ps1_path = f'{ROOT}/setup.ps1'
with open(ps1_path, 'w') as f:
    f.write(ps1_script)

subprocess.run(['powershell', ps1_path])

build_number = f'{datetime.datetime.now():%y-%m-%d_%H-%M-%S}'


# Config cx_Freeze includes.
includes = [
    'uuid',
    'json',
    'PySide6',
    'msgpack',
    'numpy',
    'PIL',]

# Launch CX_Freeze script
setup_source = os.path.expandvars(f'{HERE}/setup.py')
executable_file = os.path.expandvars(f'{PIXOLEROS_ROOT}/pixoleros/__main__.py')
icon_file = os.path.expandvars(f'{PIXOLEROS_ROOT}/pixoleros/icons/ragtime-ico.ico')

setup_file = f'{ROOT}/setup.py'
shutil.copy(setup_source, setup_file)
python_path = f'{ROOT}/{venv_name}/Scripts/python.exe'

VERSION_YAML_FILE = f'{os.path.dirname(__file__)}/version.yaml'
with open(VERSION_YAML_FILE, 'r') as f:
    version_data = yaml.full_load(f)
    version_data['build'] += 1
    if args.minor:
        version_data['minor'] += 1
    elif args.major:
        version_data['major'] += 1
        version_data['minor'] = 0


with open(f'{os.getcwd()}/build_config.json', 'w') as f:
    version = (
        f'{version_data["major"]}.{version_data["minor"]}.'
        f'{version_data["build"]}{version_data["name"]}')
    d = f'{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}'
    name = f'pixoleros-{version}-{d}'
    json.dump({
        'includes': includes,
        'executable': executable_file,
        'version': version,
        'name': name,
        'icon': icon_file}, f)

cmd = [python_path, setup_file, 'build']
subprocess.check_call(cmd, shell=True)

if not args.preserve_venv:
    shutil.rmtree(f'{ROOT}/{venv_name}')
    os.remove('setup.py')
    os.remove('setup.ps1')
    os.remove('build_config.json')


with open(VERSION_YAML_FILE, 'w') as f:
    yaml.dump(version_data, f)

lib_directory = f'{ROOT}/{name}/lib'

shutil.copytree(
    f'{PIXOLEROS_ROOT}/pixoleros',
    f'{lib_directory}/pixoleros')



destination = f'{ROOT}/{name}'
if args.create_archive:
    shutil.make_archive(
        destination,
        'zip',
        f'{ROOT}/{name}')


print("build is done ! Let's mod !")