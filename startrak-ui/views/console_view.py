
from PySide6.QtCore import QEvent, QObject, QTimer, Qt, Slot
from PySide6.QtGui import QKeyEvent
from qt.extensions import *
from qt.classes.qterm import QTerminal
from PySide6 import QtWidgets


UI_CONSOLE, _ = load_class('console_view')
class ConsoleView(QtWidgets.QFrame, UI_CONSOLE):	#type:ignore
	console_event : UIEvent
	def __init__(self, parent: QtWidgets.QWidget = None):
		super().__init__(parent)
		self.setupUi(self)
		self.console_event = UIEvent(self)

		self.terminal = get_child(self, 'terminal', QTerminal)
		self.line_input = get_child(self, 'line_input', QtWidgets.QLineEdit)
		self.terminal.set_stdin(self.line_input)
		self.mode_selector = get_child(self, 'mode_selector', QtWidgets.QComboBox)
		self.mode_selector.addItem('[ST]', 'Startrak')
		self.mode_selector.addItem('[PY]', 'Python')
		self.mode_selector.addItem('[SH]', 'Shell')
		self.mode_selector.setItemDelegate(SelectorBoxDelegate())
		self.terminal.on_sessionUpdate.connect(self.console_event('session_edit', None))
		QTimer.singleShot(500, self, self.terminal.prepare)
		
		terminal_filter = TerminalEventFilter(self)
		input_filter = InputEventFilter(self)
		self.installEventFilter(terminal_filter)
		self.line_input.installEventFilter(input_filter)

	
	@Slot(int)
	def set_mode(self, mode : int):
		match mode:
			case 0:
				self.terminal.set_language('st')
			case 1:
				self.terminal.set_language('py')
			case 2:
				self.terminal.set_language('sh')

	@Slot(str)
	def text_edited(self, text : str):
		lstrip = text.lstrip()
		if lstrip.startswith('>'):
			self.mode_selector.setCurrentIndex(1)
			self.line_input.setText(lstrip[1:])
		if lstrip.startswith('!'):
			self.mode_selector.setCurrentIndex(2)
			self.line_input.setText(lstrip[1:])

	@Slot()
	def command_sent(self):
		text = self.line_input.text()
		self.terminal.process(text)
		self.mode_selector.setCurrentIndex(0)

class TerminalEventFilter(QObject):
	def eventFilter(self, obj,  event):
		if event.type() == QEvent.Type.KeyPress:
				key = self.parent().terminal.convert_key(event)
				self.parent().terminal.on_keyEvent(key)

				if event.key() == Qt.Key.Key_Tab:
					return True
		return super().eventFilter(obj, event)
class InputEventFilter(QObject):
	def eventFilter(self, obj,  event):
		if event.type() == QEvent.Type.KeyPress:
				if event.key() == Qt.Key.Key_Tab:
					self.parent().terminal.on_keyEvent('tab')
					return True
		return super().eventFilter(obj, event)

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
