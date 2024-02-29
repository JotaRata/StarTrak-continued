from io import BytesIO, TextIOBase
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextBlockFormat
from qt.extensions import *
from PySide6 import QtWidgets

import startrak

class ConsoleView(QtWidgets.QFrame):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super().__init__(parent)
		layout = QtWidgets.QVBoxLayout(self)
		self.scroll_text = QtWidgets.QTextEdit(self)
		self.scroll_text.setReadOnly(True)
		font = QFont("Courier", 10)
		self.scroll_text.setFont(font)
		self.scroll_text.textCursor().clearSelection()
		self.scroll_text.insertPlainText('Startrak ' + startrak.VERSION + '\n')	#type:ignore
		self.scroll_text.insertPlainText('=' * 40 + '\n')

		self.input_line = QtWidgets.QLineEdit(self)
		layout.addWidget(self.scroll_text)
		layout.addWidget(self.input_line)

		self.stdout = StdoutListener()
		self.stderr = StderrListener()
		sys.stdout = self.stdout		#type: ignore
		sys.stderr = self.stderr		#type: ignore
		self.stdout.write_event.connect(self.update_console)
		self.stderr.write_event.connect(self.update_console)

		block_format = QTextBlockFormat()
		block_format.setLineHeight(1.5, 0x4)
		self.scroll_text.textCursor().setBlockFormat(block_format)

		self._globals = {val: getattr(startrak, val) for val in dir(startrak) if '__' not in val}
		self.input_line.returnPressed.connect(self.command_sent)

	def update_console(self, text : str):
		self.scroll_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)
		self.scroll_text.insertPlainText(text)
		self.scroll_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)

	def command_sent(self):
		text = self.input_line.text()
		if not text:
			return
		self.update_console('> ' + text + '\n')

		try:
			result = eval(text, self._globals)
		except SyntaxError:
			exec(text, self._globals)
			result = None
		finally:
			self.input_line.clear()

		if result:
			self.update_console(repr(result) + '\n')

class StdoutListener(QtCore.QObject):
	write_event = Signal(str)
	def __init__(self) -> None:
		super().__init__()
		self.__stdout__ = sys.stdout
	
	def write(self, s: str):
		self.__stdout__.write(s)
		if not s == '\n':
			self.write_event.emit(s + '\n')
	def flush(self):
		self.__stdout__.flush()

class StderrListener(QtCore.QObject):
	write_event = Signal(str)
	def __init__(self) -> None:
		super().__init__()
		self.__stderr__ = sys.stderr
	
	def write(self, s: str):
		self.__stderr__.write(s)
		if not s == '\n':
			self.write_event.emit(s + '\n')
	def flush(self):
		self.__stderr__.flush()
