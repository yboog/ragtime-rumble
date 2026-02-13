
from PySide6 import QtCore, QtWidgets


def get_separator(orientation=QtCore.Qt.Horizontal):
    frame_shape = (
        QtWidgets.QFrame.HLine
        if orientation == QtCore.Qt.Horizontal else
        QtWidgets.QFrame.VLine)
    frame = QtWidgets.QFrame(
        frameShape=frame_shape,
        frameShadow=QtWidgets.QFrame.Sunken)
    frame.setStyleSheet(
        f'background-color: darkGray;'
        'border: 0px transparent')
    return frame