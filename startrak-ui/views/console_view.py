
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeyEvent, QTextBlockFormat
from qt.extensions import *
from qt.classes.qterm import QTerminal
from PySide6 import QtWidgets


UI_CONSOLE, _ = load_class('console_view')
class ConsoleView(QtWidgets.QFrame, UI_CONSOLE):	#type:ignore
	mode : int
	def __init__(self, parent: QtWidgets.QWidget = None):
		super().__init__(parent)
		self.setupUi(self)

		self.terminal = get_child(self, 'terminal', QTerminal)
		self.line_input = get_child(self, 'line_input', QtWidgets.QLineEdit)
		self.mode_selector = get_child(self, 'mode_selector', QtWidgets.QComboBox)
		block_format = QTextBlockFormat()
		block_format.setLineHeight(1.5, 0x4)
		self.terminal.textCursor().setBlockFormat(block_format)

	def keyPressEvent(self, event: QKeyEvent):
		key = self.terminal.convert_key(event)
		self.terminal.on_keyEvent(key)
		return super().keyPressEvent(event)
	
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
		self.terminal.process(text)
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
