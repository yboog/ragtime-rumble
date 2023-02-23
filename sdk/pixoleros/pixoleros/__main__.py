import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PySide6 import QtWidgets
from pixoleros.mainwindow import Pixoleros
from pixoleros.io import get_icon

app = QtWidgets.QApplication([])
css_filepath = (f'{os.path.dirname(__file__)}/flatdark.css')
with open(css_filepath, 'r') as f:
    css = f.read()
app.setWindowIcon(get_icon('ragtime-ico.ico'))
app.setStyleSheet(css)
window = Pixoleros()

if len(sys.argv) > 1:
    for filepath in sys.argv[1:]:
        window.open_filepath(filepath)

window.show()
sys.exit(app.exec())
