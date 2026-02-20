# Command to build: python setup.py build
from cx_Freeze import setup, Executable
import os
import shutil


build_exe_options = {
    "excludes": [
        "tkinter", "unittest", "email", "pkg_resources", "xml", "pydoc_data",
        "PyQt5", "PySide2", "PyQt6", "pyexpat", "ctypes", "pandas",
        "matplotlib", "shibocken", "shiboken2", "sip", "sip2", "sip6",
        "pygame", "scipy", "test", "setuptools", "pytest", "pygments"]}

qt_folder_excludes = [
    "resources",
    "examples",
    "translations",
    "qml",
    "glue",
    "scripts",
    "support",
    "include",
    "typesystems",
    "plugins/assetimporters",
    "plugins/canbus",
    "plugins/designer",
    "plugins/generic",
    "plugins/geometryloaders",
    "plugins/sceneparsers",
    "plugins/scxmldatamodel",
    "plugins/sensors",
    "plugins/sqldrivers",
    "plugins/tls",
    "plugins/virtualkeyboard",
    "plugins/webview",
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
    "Qt6WebEngineCore.dll",
    "Qt6UiTools.dll",
    "Qt6ChartsQml.dll",
    "Qt6Multimedia.dll",
    "Qt6Quick3D.dll",
    "Qt6Bluetooth.dll",
    "Qt6Bodymovin.dll",
    "Qt6Charts.dll",
    "Qt6Concurrent.dll",
    "Qt6Core5Compat.dll",
    "Qt6DBus.dll",
    "Qt6Designer.dll",
    "Qt6DesignerComponents.dll",
    "opengl32sw.dll",
    "QtOpenGL.pyd",
    "d3dcompiler_47.dll",
    "Qt6Quick.dll",
    "Qt6ShaderTools.dll",
    "Qt63DRender.dll",
    "Qt6OpenGL.dll",

]


setup(
    name="Pixoleros",
    author="Jean-Loup Comby & Lionel Brouyère",
    options={"build_exe": build_exe_options},
    executables=[Executable('pixoleros/__main__.py', base="Win32GUI")])


current = os.path.dirname(__file__)
desktop = os.path.expanduser("~/Desktop")
deployroot = os.path.join(desktop, "pixoleros")
src = os.path.join(current, "build/exe.win-amd64-3.10")

for folder in qt_folder_excludes:
    directory = f'{src}/lib/PySide6/{folder}'
    if os.path.exists(directory):
        shutil.rmtree(directory)

for filename in qt_file_excludes:
    filename = f'{src}/lib/PySide6/{filename}'
    if os.path.exists(filename):
        os.remove(filename)

os.makedirs(deployroot)
file_names = os.listdir(src)
for file_name in file_names:
    shutil.move(os.path.join(src, file_name), deployroot)

os.rename(
    os.path.join(deployroot, "__main__.exe"),
    os.path.join(deployroot, "pixoleros.exe"))

os.makedirs(os.path.join(deployroot, "pixoleros"))
os.rename(
    os.path.join(deployroot, "lib", "pixoleros", "flatdark.css"),
    os.path.join(deployroot, "pixoleros", "flatdark.css")
)

# shutil.copytree(
#     src=os.path.join(current, "resources"),
#     dst=os.path.join(gameroot, "lib/resources"))

# import shutil
# shutil.make_archive(gameroot, 'zip', desktop, 'game.zip')