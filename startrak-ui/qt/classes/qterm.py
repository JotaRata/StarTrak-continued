from importlib.machinery import SourceFileLoader
import os
import sys
from typing import Callable

from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QTextEdit, QWidget

sys.path.append(os.getcwd() + '/startrak-cl')
consoleapp = SourceFileLoader('consoleapp', 'startrak-cl/console/consoleapp.py').load_module()
ConsoleApp = consoleapp.ConsoleApp

class QTerminal(ConsoleApp, QTextEdit):
	def __init__(self, parent : QWidget) -> None:
		QTextEdit.__init__(self, parent)
		ConsoleApp.__init__(self,)

		self.output = TerminalOutput(self)
		sys.stdout = self.output
		# sys.stderr = self.output

	def size(self):
		line_width = self.fontMetrics().lineWidth()
		line_height = self.fontMetrics().height()
		return self.height() // line_height, self.width() // line_width

	def on_keyEvent(self, key : str):
		if self._input_mode == 'action':
			self.process_action(key)
			return

	def convert_key(self, event : QKeyEvent) -> str:
		match event.key():
			case Qt.Key.Key_Enter | Qt.Key.Key_Return:
				key = 'enter'
			case Qt.Key.Key_Space:
				key = 'space'
			case Qt.Key.Key_Backspace:
				key = 'backspace'
			case Qt.Key.Key_Delete:
				key = 'del'
			case Qt.Key.Key_Tab:
				key = 'tab'
			case Qt.Key.Key_Insert:
				key = 'insert'
			case Qt.Key.Key_Escape:
				key = 'esc'
			case Qt.Key.Key_Up:
				key = 'up'
			case Qt.Key.Key_Down:
				key = 'down'
			case Qt.Key.Key_Left:
				key = 'left'
			case Qt.Key.Key_Right:
				key = 'right'
			case _:
				key = event.text()
		return key
	
class TerminalOutput:
	def __init__(self, parent : QTextEdit) -> None:
		self.parent = parent

	def write(self, string : str):
		self.parent.insertPlainText(string)
		self.parent.moveCursor(QtGui.QTextCursor.MoveOperation.End)
	def flush(self):
		pass
	def read(self):
		return self.parent.toPlainText()
	def getvalue(self):
		return self.read()
	def clear(self):
		QTextEdit.clear(self.parent)
