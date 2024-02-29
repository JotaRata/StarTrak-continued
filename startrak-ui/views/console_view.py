from io import BytesIO, TextIOBase
import os
import sys

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextBlockFormat
from qt.extensions import *
from PySide6 import QtWidgets

import startrak

UI_CONSOLE, _ = load_class('console_view')
class ConsoleView(QtWidgets.QFrame, UI_CONSOLE):	#type:ignore
	mode : int
	def __init__(self, parent: QtWidgets.QWidget = None):
		super().__init__(parent)
		self.setupUi(self)

		self.scroll_text = get_child(self, 'scroll_text', QtWidgets.QTextEdit)
		self.line_input = get_child(self, 'line_input', QtWidgets.QLineEdit)
		self.mode_selector = get_child(self, 'mode_selector', QtWidgets.QComboBox)

		# todo: replace with actual output from Startrak CL
		self.scroll_text.textCursor().clearSelection()
		self.scroll_text.insertPlainText('Startrak ' + startrak.VERSION + '\n')	#type:ignore
		self.scroll_text.insertPlainText('=' * 40 + '\n')

		self.stdout = StdoutListener()
		self.stderr = StderrListener()
		sys.stdout = self.stdout		#type: ignore
		sys.stderr = self.stderr		#type: ignore
		self.stdout.write_event.connect(self.update_console)
		self.stderr.write_event.connect(self.update_console)

		self.mode = 0
		self.mode_selector.addItem('>', 'Python')
		self.mode_selector.addItem('!', 'Bash/CMD')
		self.mode_selector.setItemDelegate(SelectorBoxDelegate())

		block_format = QTextBlockFormat()
		block_format.setLineHeight(1.5, 0x4)
		self.scroll_text.textCursor().setBlockFormat(block_format)
		self._globals = {val: getattr(startrak, val) for val in dir(startrak) if '__' not in val}

	def update_console(self, text : str):
		self.scroll_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)
		self.scroll_text.insertPlainText(text)
		self.scroll_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)

	@Slot(int)
	def set_mode(self, mode : int):
		self.mode = mode

	@Slot(str)
	def text_edited(self, text : str):
		lstrip = text.lstrip()
		if lstrip.startswith('>'):
			self.mode_selector.setCurrentIndex(0)
			self.line_input.setText(lstrip[1:])
		if lstrip.startswith('!'):
			self.mode_selector.setCurrentIndex(1)
			self.line_input.setText(lstrip[1:])

	@Slot()
	def command_sent(self):
		text = self.line_input.text()
		if self.mode == 0:
			if not text:
				self.update_console('> ' + '\n')
				return
			self.update_console('> ' + text + '\n')
			try:
				result = eval(text, self._globals)
			except SyntaxError:
				exec(text, self._globals)
				result = None
			finally:
				self.line_input.clear()
			if result:
				self.update_console(repr(result) + '\n')
		
		elif self.mode == 1:
			if not text:
				return
			self.update_console('! ' + text + '\n')
			result = os.popen(text).read()
			if result:
				self.update_console(result + '\n')
			self.line_input.clear()
			self.mode_selector.setCurrentIndex(0)

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

class SelectorBoxDelegate(QtWidgets.QStyledItemDelegate):
	def paint(self, painter, option, index):
		text = index.data(Qt.ItemDataRole.DisplayRole)
		symbol = index.data(Qt.ItemDataRole.UserRole)
		
		comboBoxStyle = QtWidgets.QStyleOptionComboBox()
		comboBoxStyle.initFrom(option.widget)
		comboBoxStyle.currentText = symbol
		comboBoxStyle.rect = option.rect
		comboBoxStyle.state |= QtWidgets.QStyle.State_Enabled
		QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, comboBoxStyle, painter)
