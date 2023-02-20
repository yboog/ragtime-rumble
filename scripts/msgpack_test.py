from PySide6 import QtGui, QtCore
import os
import msgpack
import tempfile


folder = tempfile.gettempdir()
with open(f'{folder}/testmsgpack', 'wb') as f:
    # convert QPixmap to bytes
    image = QtGui.QImage(r'C:\perso\drunk-paranoia\drunkparanoia\resources\vfx\coin-alert.png')
    ba = QtCore.QByteArray()
    buff = QtCore.QBuffer(ba)
    buff.open(QtCore.QIODevice.WriteOnly)
    ok = image.save(buff, "PNG")
    pixmap_bytes = ba.data()
    msgpack.dump([pixmap_bytes], f)
