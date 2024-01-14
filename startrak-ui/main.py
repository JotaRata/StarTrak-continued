from PySide6.QtWidgets import QApplication
from utils import *

if __name__ == "__main__":
	app = QApplication([])
	app.setStyle('Fusion')

	with read_layout('main_layout') as f:
		main = create_widget(f)
		main.show()
	app.exec()
else:
	raise ImportError('Cannot import module')