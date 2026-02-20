import os
import sys
sys.path.append('c:/perso/ragtime-rumble/sdk/')

from PySide6 import QtWidgets
from pixaloon.mainwindow import Pixaloon


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = Pixaloon()
    for arg in sys.argv:
        if arg.endswith('.json'):
            window.open_document(arg)
    window.show()
    import os
    stylesheet_filepath = f'{os.path.dirname(__file__)}/css/flatdark.css'
    with open(stylesheet_filepath, 'r') as f:
        app.setStyleSheet(f.read())
    app.setStyle('fusion')
    app.exec()


# py -3.12 c:\perso\ragtime-rumble\sdk\pixaloon C:\perso\ragtime-rumble\ragtimerumble\resources\scenes\saloon.json C:\perso\ragtime-rumble\ragtimerumble\resources\scenes\street.json