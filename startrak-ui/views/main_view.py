from __future__ import annotations
from PySide6 import QtCore, QtWidgets 
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMessageBox
from qt.extensions import *
from views.application import Application
from views.session_view import SessionTreeView
from views.inspectors import InspectorView

UI_MainWindow, _ = load_class('main_layout')

class MainView(QtWidgets.QMainWindow, UI_MainWindow):	#type: ignore[valid-type, misc]
	session_view : SessionTreeView
	inspector_view : InspectorView

	def __init__(self,parent: QtWidgets.QWidget | None = None, flags = None) -> None:
		super().__init__(parent)
		# with read_layout('main_layout') as f:
		# 	self.main_window = create_widget(f)
		self.setupUi(self)
		view_frame = get_child(self, 'content_l', QtWidgets.QFrame)
		self.session_view = SessionTreeView(view_frame)
		view_frame.layout().addWidget(self.session_view)


		sidebar_frame = get_child(self, 'widget_sidebar', QtWidgets.QFrame)
		self.inspector_view = InspectorView(sidebar_frame)
		sidebar_frame.layout().addWidget(self.inspector_view)

		self.session_view.clicked.connect(self.inspector_view.on_sesionViewUpdate)
		self.inspector_view.on_inspectorUpdate.connect(self.session_view.updateItem)
		self.inspector_view.on_inspectorSelect.connect(self.session_view.setCurrentIndex)
		self.inspector_view.on_inspectorSelect.connect(self.session_view.expandParent)
		self.fix_splitterWidth() 
		# self.show()
	
	@QtCore.Slot(QAction)
	def menubar_call(self, code: QAction):
		app = Application.instance()
		match code.objectName():
			case 'action_new':
				prev_session = app.st_module.get_session()
				# todo: Check whether the session has unsaved changes
				safe = not prev_session or prev_session.name == 'default'
				if not safe:
					msg = QMessageBox.warning(self, 'Discard session',
											'A session already exists. Do you want to discard it?',
											QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Discard)
					safe = msg == QMessageBox.StandardButton.Discard
				if safe:
					session = app.st_module.new_session('default')
					app.on_sessionLoad.emit(session)

			case 'action_open':
				path, _ = QFileDialog.getOpenFileName(self, 'Open session', filter= 'Startrak session (*.trak)')
				session = app.st_module.load_session(path)
				app.on_sessionLoad.emit(session)
			case _:
				pass
	def fix_splitterWidth(self):
		splitter_h = get_child(self, 'splitter_subh', QtWidgets.QSplitter)
		splitter_h.setSizes([splitter_h.size().width() // 2, 
							splitter_h.size().width() // 2])
