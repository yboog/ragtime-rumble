# Command to build: python setup.py build
from cx_Freeze import setup, Executable
import os
import shutil


build_exe_options = {
    "excludes": [
        "tkinter", "unittest", "email", "pkg_resources", "xml", "pydoc_data",
        "PyQt5", "PyQt6", "pyexpat", "ctypes", "pandas", "shiboken2",
        "sip", "sip2", "sip6", "pygame"]}

qt_folder_excludes = [
    "resources",
    "examples",
    "translations"
]

qt_file_excludes = [
    "assistant.exe",
    "designer.exe",
    "lconvert.exe",
    "linguist.exe",
    "lrelease.exe",
    "lupdate.exe",
    "qtdiag.exe",
    "QtWebEngineProcess.exe",
    "rcc.exe",
    "uic.exe",
    "opengl32sw.dll",
    "d3dcompiler_47.dll",
    "Qt6Qml.dll",
    "Qt6ShaderTools.dll",
    "Qt63DRender.dll",
    "Qt6OpenGL.dll",
    "Qt6VirtualKeyboard.dll",
    "Qt6Multimedia.dll",
    "Qt6Quick3D.dll",
    "Qt6UiTools.dll",
    "Qt6Bluetooth.dll",
    "Qt6Bodymovin.dll",
    "Qt6Charts.dll",
    "Qt6ChartsQml.dll",
    "Qt6Concurrent.dll",
    "Qt6Core5Compat.dll",
    "Qt6DBus.dll",
    "Qt6Designer.dll",
    "Qt6DesignerComponents.dll",
    "Qt6WebEngineCore.dll"
]

setup(
    name="Pixoleros",
    author="Jean-Loup Comby & Lionel Brouyère",
    options={"build_exe": build_exe_options},
    executables=[Executable('pixoleros/__main__.py')])


current = os.path.dirname(__file__)
desktop = os.path.expanduser("~/Desktop")
gameroot = os.path.join(desktop, "pixoleros")
src = os.path.join(current, "build/exe.win-amd64-3.10")

for folder in qt_folder_excludes:
    shutil.rmtree(f'{src}/lib/PySide6/{folder}')

# for filename in qt_file_excludes:
#     os.remove(f'{src}/lib/PySide6/{filename}')

os.makedirs(gameroot)
file_names = os.listdir(src)
for file_name in file_names:
    shutil.move(os.path.join(src, file_name), gameroot)

os.rename(
    os.path.join(gameroot, "__main__.exe"),
    os.path.join(gameroot, "pixoleros.exe"))

# shutil.copytree(
#     src=os.path.join(current, "resources"),
#     dst=os.path.join(gameroot, "lib/resources"))

# import shutil
# shutil.make_archive(gameroot, 'zip', desktop, 'game.zip')