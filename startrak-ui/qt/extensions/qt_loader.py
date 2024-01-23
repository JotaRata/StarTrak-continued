from contextlib import contextmanager
from pathlib import Path
from typing import cast
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader, loadUiType
from PySide6.QtCore import QFile, QIODevice

BASE_DIR = Path(__file__).parent.parent
STUI_DIR = BASE_DIR / 'layouts/'


@contextmanager
def load_layout(name : str):
	ui_file = QFile( str(STUI_DIR / name) + '.ui')
	try:
		ui_file.open(QIODevice.OpenModeFlag.ReadOnly)
		yield ui_file
	except RuntimeError:
		print('Invalid path', str(STUI_DIR / name) + '.ui')
	finally:
		ui_file.close()

def load_class(name : str):
	ui_file = str(STUI_DIR / name) + '.ui'
	return cast(tuple[type, type], loadUiType(ui_file))
	
def create_widget(ui_file : QFile):
	loader = QUiLoader()
	return loader.load(ui_file, None)
