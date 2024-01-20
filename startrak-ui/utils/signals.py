
from PySide6.QtWidgets import QFileDialog


def open_sessionDialog(st_module, main_window):
	path, _ = QFileDialog.getOpenFileName(main_window, 'Open session', filter= 'Startrak session (*.trak)')
	st_module.load_session(path)