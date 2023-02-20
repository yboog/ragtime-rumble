import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PySide6 import QtWidgets
from pixoleros.mainwindow import SpritesheetEditor

app = QtWidgets.QApplication([])
window = SpritesheetEditor()
window.show()
sys.exit(app.exec())