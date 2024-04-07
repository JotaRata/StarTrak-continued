from importlib.machinery import SourceFileLoader
import os
import platform
import re
import sys
from typing import Callable

from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextBlockFormat
from PySide6.QtWidgets import QLineEdit, QTextEdit, QWidget

import startrak

sys.path.append(os.getcwd() + '/startrak-cl')
consoleapp = SourceFileLoader('consoleapp', 'startrak-cl/console/consoleapp.py').load_module()
ConsoleApp = consoleapp.ConsoleApp
_PREFIXES = consoleapp._PREFIXES

class QTerminal(ConsoleApp, QTextEdit):
	on_sessionUpdate = Signal()
	def __init__(self, parent : QWidget) -> None:
		QTextEdit.__init__(self, parent)
		# ConsoleApp.__init__(self,)
		block_format = QTextBlockFormat()
		block_format.setLineHeight(1.5, 0x4)
		self.textCursor().setBlockFormat(block_format)

		self.output = QTerminalOutput(self)
		sys.stdout = self.output
		sys.stderr = self.output

	def prepare(self):
		self.output.write(f'Current working directory: {os.path.basename(os.getcwd())}/\n')
		self.output.write(f'Version: {startrak.VERSION} {platform.platform()} python {platform.python_version()} \n')
		self.output.write('Welcome to startrak.\n')

		self.output.write(' \n' * (self.size()[0] - 4))
	
	def set_stdin(self, input : QLineEdit):
		self.input = QterminalInput(input)
		self.set_language('st')
		self.set_mode('text')
	
	def size(self):
		line_width = self.fontMetrics().horizontalAdvance('A') + 1
		line_height = self.fontMetrics().height()
		return self.height() // line_height, self.width() // line_width

	def on_keyEvent(self, key : str):
		if self._input_mode == 'action':
			self.process_action(key)
		elif self._input_mode == 'text':
			if not self.input.parent.hasFocus():
				self.input.write(key)
				self.input.parent.setFocus()
		
	def process(self, string : str):
		prompt = _PREFIXES[self._language_mode]
		self.output.write(f'<b>{prompt}</b>')
		self.output.write(string + '<br>')
		super().process(string)
		self.input.clear()

		if string.startswith('add') or \
			string.startswith('del') or \
			string.startswith('open') or \
			(string.startswith('session') and '-new' in string):
			self.on_sessionUpdate.emit()
	
	def set_mode(self, mode : str, **kwargs):
		old_mode = getattr(self, '_input_mode', 'text')
		super().set_mode(mode, **kwargs)
		if mode == 'text':
			self.input.parent.setReadOnly(False)
			self.input.parent.setFocus()
			self.input.parent.parent().show()
		elif mode == 'action':
			self.input.parent.parent().hide()
			self.input.parent.setReadOnly(True)
			self.parent().setFocus()
		if mode == 'text' and old_mode == 'action':
			self.on_sessionUpdate.emit()
			
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
	
	def format(self, text : str, format : str):
		match format:
			case 'bold':
				return f'<b>{text}</b>'
			case 'underline':
				return f'<u>{text}</u>'
			case 'highlight':
				return f'<span style="background-color: #f0f0f0; color: #000000;"> {text} </span>'
			case _:
				return text
	
class QTerminalOutput:
	def __init__(self, parent : QTextEdit) -> None:
		self.parent = parent

	def write(self, string : str):
		html = string.replace('\n', '<br>').replace('  ', "&nbsp; ")
		# html = re.sub(r" {4,}", "&nbsp;", html)

		self.parent.insertHtml(html)
		self.parent.moveCursor(QtGui.QTextCursor.MoveOperation.End)
	def flush(self):
		pass
	def read(self):
		return self.parent.toPlainText()
	def getvalue(self):
		return self.read()
	def clear(self):
		QTextEdit.clear(self.parent)

class QterminalInput:
	def __init__(self, parent : QLineEdit) -> None:
		self.parent = parent

	def write(self, string : str):
		self.parent.insert(string)
	def flush(self):
		pass
	def read(self):
		return self.parent.text()
	def getvalue(self):
		return self.read()
	def clear(self):
		QLineEdit.clear(self.parent)