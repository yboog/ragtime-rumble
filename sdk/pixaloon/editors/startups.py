from PySide6 import QtWidgets
from pixaloon.selection import Selection
from pixaloon.editors.base import BaseEditor


class StartupsEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)