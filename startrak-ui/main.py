from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

file_path = Path(__file__).parent
if __name__ == "__main__":
	app = QApplication([])
	app.setStyle('Fusion')
	ui_file = QFile(str(file_path / 'ui/main_layout.ui'))
	ui_file.open(QIODevice.OpenModeFlag.ReadOnly)
	
	loader = QUiLoader()
	main_window = loader.load(ui_file, None)
	main_window.show()
	ui_file.close()
	app.exec()
