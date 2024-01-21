
from PySide6 import QtCore
from PySide6.QtWidgets import QFileDialog

def on_sessionLoad(st_module, main_window):
	path, _ = QFileDialog.getOpenFileName(main_window, 'Open session', filter= 'Startrak session (*.trak)')
	st_module.load_session(path)