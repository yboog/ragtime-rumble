# Command to build: python setup.py build

import sys
from cx_Freeze import setup, Executable
import os
import shutil


build_exe_options = {
    "excludes": [
        "tkinter", "unittest", "email", "pkg_resources", "xml", "pydoc_data", "PySide6",
        "PyQt5", "PySide2", "PyQt6", "pyexpat", "ctypes", "pandas", "shiboken2",
        "sip", "sip2", "shiboken6", "sip6", "numpy"]}

setup(
    name="Drunk-o-Therapia",
    author="Jean-Loup Comby & Lionel Brouyère",
    options={"build_exe": build_exe_options},
    executables=[Executable('drunkparanoia/__main__.py')])


current = os.path.dirname(__file__)
desktop = os.path.expanduser("~/Desktop")
gameroot = os.path.join(desktop, "drunkotherapie")
src = os.path.join(current, "build/exe.win-amd64-3.10")
os.makedirs(gameroot)
file_names = os.listdir(src)
for file_name in file_names:
    shutil.move(os.path.join(src, file_name), gameroot)

os.rename(
    os.path.join(gameroot, "__main__.exe"),
    os.path.join(gameroot, "game.exe"))

shutil.copytree(
    src=os.path.join(current, "resources"),
    dst=os.path.join(gameroot, "lib/resources"))

# import shutil
# shutil.make_archive(gameroot, 'zip', desktop, 'game.zip')