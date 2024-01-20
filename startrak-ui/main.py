# mypy: disable-error-code="attr-defined"
import sys, os
sys.path.insert(0, os.getcwd())
import startrak
from PySide6.QtGui import QAction
from PySide6 import QtWidgets, QtCore
from utils import *
from classes import SessionTreeModel

def setup_sessionView(session_view):
	model = SessionTreeModel(startrak.get_session())
	session_view.setModel(model)
	session_view.expand(model.index(0, 0, QtCore.QModelIndex()))

if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	app.setStyle('Fusion')
	with read_layout('main_layout') as f:
		main = create_widget(f)
		splitter = get_child(main, 'splitter_subh', QtWidgets.QSplitter)
		splitter.setSizes([splitter.size().width() // 2, 
                        splitter.size().width() // 2])
		session_view = get_child(splitter, 'session_view', QtWidgets.QTreeView, )
		setup_sessionView(session_view)

		label = get_child(main, 'label_info', QtWidgets.QLabel)
		session_view.clicked.connect( lambda index:  label.setText(index.internalPointer().ref.__pprint__(0,2)) )

		action_openSession = get_child(main, 'action_open', QAction)
		action_openSession.triggered.connect(lambda: signals.open_sessionDialog(startrak, main))
		action_openSession.triggered.connect(lambda: setup_sessionView(session_view))
		main.show()
	app.exec()
else:
	raise ImportError('Cannot import module')