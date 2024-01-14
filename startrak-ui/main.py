import os, sys
sys.path.insert(0, os.getcwd())
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

		
if __name__ == "__main__":
	app = QApplication([])
	ui_file = QFile("startrak-ui/qt/template/main.ui")
	ui_file.open(QIODevice.ReadOnly)
	
	loader = QUiLoader()
	main_window = loader.load(ui_file, None)
	main_window.show()
	ui_file.close()
	app.exec()
