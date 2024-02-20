from __future__ import annotations
from typing import Any
from PySide6 import QtCore, QtWidgets 
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMessageBox
from qt.extensions import *
from .application import Application
from .session_view import SessionTreeView
from .inspectors import InspectorView
from .image_view import ImageViewer

UI_MainWindow, _ = load_class('main_layout')
class MainView(QtWidgets.QMainWindow, UI_MainWindow):	#type: ignore[valid-type, misc]
	image_view : ImageViewer
	session_view : SessionTreeView
	inspector_view : InspectorView

	def __init__(self) -> None:
		super().__init__(None)
		# with read_layout('main_layout') as f:
		# 	self.main_window = create_widget(f)
		self.setupUi(self)

		frame_viewer = get_child(self, 'frame_viewer', QtWidgets.QFrame)
		self.image_view = ImageViewer(frame_viewer)
		frame_viewer.layout().addWidget(self.image_view)

		content_left = get_child(self, 'content_left', QtWidgets.QFrame)
		self.session_view = SessionTreeView(content_left)
		content_left.layout().addWidget(self.session_view)

		sidebar_frame = get_child(self, 'widget_sidebar', QtWidgets.QFrame)
		self.inspector_view = InspectorView(sidebar_frame)
		sidebar_frame.layout().addWidget(self.inspector_view)

		self.session_view.clicked.connect(self.inspector_view.on_sesionViewUpdate)
		self.session_view.doubleClicked.connect(self.image_view.on_itemSelected)
		self.inspector_view.inspector_event += self.on_inspectorEvent

		#todo: replace all signals by a single event handler
		# self.inspector_view.on_inspectorUpdate.connect(self.session_view.updateItem)
		# self.inspector_view.on_inspectorUpdate.connect(self.image_view.update_image)
		# self.inspector_view.on_inspectorSelect.connect(self.session_view.setCurrentIndex)
		# self.inspector_view.on_inspectorSelect.connect(self.session_view.expandParent)
		# self.image_view.on_starSelected.connect(self.session_view.setCurrentIndex)
		self.image_view.on_starSelected.connect(self.inspector_view.on_sesionViewUpdate)
		self.fix_splitterWidth() 

	#todo: improve event codes (i.e. a StrEnum)
	def on_inspectorEvent(self, code : EventCode, value : Any):
		match code:
			case 'update_image':
				self.image_view.on_itemSelected(value)
			case 'session_focus':
				self.session_view.setCurrentIndex(value)
				self.session_view.expandParent(value)
			case 'inspector_update':
				self.session_view.updateItem(value[0], value[1])
				self.image_view.update_image(value[0], value[1])
			case _:
				print('Invalid code', code)

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
