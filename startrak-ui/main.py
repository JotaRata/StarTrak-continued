import sys, os
sys.path.insert(0, os.getcwd())
import startrak
from PySide6 import QtWidgets, QtCore
from utils import *
from classes import SessionTreeModel

if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	app.setStyle('Fusion')

	with read_layout('main_layout') as f:
		main = create_widget(f)
		splitter = get_child(main, 'splitter_subh', QtWidgets.QSplitter)
		splitter.setSizes([splitter.size().width() // 2, 
                        splitter.size().width() // 2])
		session_view = get_child(splitter, 'session_view', QtWidgets.QTreeView, )
		
		model = SessionTreeModel()
		session_view.setModel(model)
		main.show()
	app.exec()
else:
	raise ImportError('Cannot import module')