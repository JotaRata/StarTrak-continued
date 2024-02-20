from enum import StrEnum
import re
from typing import Any, List, Literal, Type, TypeVar, cast, overload
from PySide6 import QtWidgets, QtCore, QtGui

TWdg = TypeVar('TWdg', bound= QtCore.QObject)
T = TypeVar('T')

def get_child(parent : QtWidgets.QWidget, name: str, _type : Type[TWdg]) -> TWdg:
	return cast(TWdg, parent.findChild(_type, name))

class QStyleSheet:
	__slots__ = ('sheet', 'variables')
	sheet : str
	variables : dict[str, str]

	def __init__(self, path) -> None:
		invalid_syntax = Exception('Invalid syntax')
		stylesheet = ''
		with open(path, 'r') as file:
			# Block posidion code:
			# Its used to make sure the syntax is consistent with the rest of the file (I know there are better ways)
			root_block = 0	# 0= No parsing done yet
			self.variables = dict[str, str]()	# Create an empty dictionary to store the variables

			for line in file:
				if ':root' in line:
					root_block = 1 		# 1= :root label found, expecting opening bracket
				if '{' in line:
					if root_block == 1:
						root_block = 2 	# 2= opening brakcet found, the block is "safe" to read
						continue
					else:
						raise invalid_syntax
				if '}' in line:			# If the closing bracket is found, check the opening bracket has been found first
					if root_block != 2:	# If not the case, throw an error
						raise invalid_syntax
					else:
						stylesheet = file.read()
						break
				if root_block == 2:
					split = line.split(':')

					match split:
						case  [key, value]:
							self.variables[key.strip()] = value.strip()
						case _:
							raise invalid_syntax
		pattern = re.compile('@(' + '|'.join(sorted(self.variables, key= len, reverse=True)).strip('|') + ')')
		self.sheet = pattern.sub(lambda match: self.variables[match.group(1)], stylesheet)
	
	def get_color(self, name):
		value = self.variables.get(name, '#FFFFFF')
		if 'rgb' in value:
			idx_l = value.index('(')+1
			idx_r = value.rindex(')')
			return QtGui.QColor( *[int(s) for s in value[idx_l:idx_r].split(',')])
		return QtGui.QColor(value)
	
	@overload
	def __getitem__(self, key : str) -> str: ...
	@overload
	def __getitem__(self, key : tuple[str, T]) -> T: ...
	def __getitem__(self, key : str | tuple[str, T]) -> str | T:
		if type(key) is str:
			return self.variables[key]
		elif type(key) is tuple and len(key) == 2:
			cls = key[1]
			assert type(cls) is type
			return cls(self.variables[key[0]])
		else:
			raise TypeError('Invalid argument')
	def __repr__(self) -> str:
		return self.sheet

EventCode = Literal[ 
							'session_expand',		# Used to tell SessionView to expand on an item, value: QModelIndex
							'session_focus',	# Tell InspectorView to focus on the specified item, value: QModelIndex
							'inspector_update',	# Sent by InspectorView to tell that a value has changed, value: (QModelIndex, STObject)
							'update_image'		# Used to update the current image in ImageView, value: QModelIndex (file)
							]

class UIEvent(QtCore.QObject):
	__int = QtCore.Signal(str, object)

	@overload
	def __call__(self, code : Literal['session_expand', 'update_image', 'session_focus'], value : QtCore.QModelIndex): ...
	@overload
	def __call__(self, code : Literal['inspector_update'], value : tuple[QtCore.QModelIndex, Any]): ...

	def __call__(self, code : EventCode, value : Any):
		def wrapper(*args, **kwargs):
			self.__int.emit(code, value)
		return wrapper
	
	def __iadd__(self, slot: object):
		self.__int.connect(slot)
		return self
	