from io import BytesIO, TextIOBase
import os
import subprocess
import sys

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextBlockFormat
from qt.extensions import *
from PySide6 import QtWidgets
from importlib.machinery import SourceFileLoader
import startrak

sys.path.append(os.getcwd() + '/startrak-cl')
qterm = SourceFileLoader('qterm', 'startrak-cl/console/qterm.py').load_module()
QTerminal = qterm.QTerminal

UI_CONSOLE, _ = load_class('console_view')
class ConsoleView(QtWidgets.QFrame, UI_CONSOLE):	#type:ignore
	mode : int
	def __init__(self, parent: QtWidgets.QWidget = None):
		super().__init__(parent)
		self.setupUi(self)

		self.console_text = get_child(self, 'scroll_text', QtWidgets.QTextEdit)
		self.line_input = get_child(self, 'line_input', QtWidgets.QLineEdit)
		self.mode_selector = get_child(self, 'mode_selector', QtWidgets.QComboBox)
		block_format = QTextBlockFormat()
		block_format.setLineHeight(1.5, 0x4)
		self.console_text.textCursor().setBlockFormat(block_format)

		def on_write():
			self.console_text.clear()
			self.console_text.setText(self.console.read())
			self.console_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)
		self.console = QTerminal(write_event= on_write)
		# self.console.process('connect')
		
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
		self.console.process(text)
		self.line_input.clear()


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
