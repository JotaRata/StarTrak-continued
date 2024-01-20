from typing import Type, TypeVar, cast
from PySide6 import QtWidgets, QtCore

TWdg = TypeVar('TWdg', bound= QtCore.QObject)
def get_child(parent : QtWidgets.QWidget, name: str, _type : Type[TWdg]) -> TWdg:
	return cast(TWdg, parent.findChild(_type, name))

# Inject custom findChild method