from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QIcon, QMouseEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QWidget
import startrak.native
import startrak.native.ext

from views.application import Application
from qt.extensions import *
from startrak.native.ext import STObject

class SessionTreeView(QtWidgets.QTreeView):
	session_event : UIEvent

	def __init__(self, parent: QWidget | None = None) -> None:
		super().__init__(parent)
		self.session_event = UIEvent(self)
		app = Application.instance()
		app.on_sessionLoad.connect(self.setModel)

		self.session = app.st_module.get_session()
		self.setModel(self.session)
	
	def setModel(self, session):
		model = SessionModel(session)
		super().setModel(model)
		self.expand(model.index(0, 0, QtCore.QModelIndex()))
	
	def model(self) -> SessionModel:
		return cast(SessionModel, super().model())
	
	def updateItem(self, index : QModelIndex):
		obj = get_data(index)
		item = self.model().itemFromIndex(index)
		item.setData(obj.name, Qt.ItemDataRole.DisplayRole)
		item.setData(obj, Qt.ItemDataRole.UserRole)
		# self.model().dataChanged.emit(index, index)
	
	def addItem(self, obj : Any):
		model = self.model()
		session_idx = QtCore.QModelIndex()
		rows = model.rowCount(session_idx)
		if type(obj) is startrak.native.FileInfo:
			fileList_index = model.index(rows - 2, 0, session_idx)
			self.session.add_file(obj)
			model.insertRow(0, fileList_index)
			model.setData(model.index(0, 0, fileList_index), obj)

	def expandParent(self, index : QtCore.QModelIndex):
		self.expand(index.parent())

	def mousePressEvent(self, event: QMouseEvent) -> None:
		super().mousePressEvent(event)
		index = self.currentIndex()
		self.session_event('session_focus', index)()
	
	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		super().mouseDoubleClickEvent(event)
		index = self.currentIndex()
		self.session_event('update_image', index)()
		
_excluded = ['SessionLocationBlock']
class SessionModel(QStandardItemModel):
	def __init__(self, session : startrak.native.Session):
		super().__init__()
		self.rootItem = self.add_item(session, session.name)
		self.appendRow(self.rootItem)
		self.build_tree(session, self.rootItem)

	def add_item(self, obj : Any, name : str = None):
		item = QStandardItem()
		if not name:
			name = type(obj).__name__
		item.setData(name, Qt.ItemDataRole.DisplayRole)
		item.setData(obj, Qt.ItemDataRole.UserRole)
		return item
	
	def build_tree(self, item : startrak.native.ext.STObject, parent_item : QStandardItem):
		for key, value in item.__export__().items():
			if isinstance(value, STObject) and type(value).__name__ not in _excluded:
				if key.isdigit():
					key = value.name
				else:
					key = key.replace('_', ' ').capitalize()
				child_item = self.add_item(value, key)
				parent_item.appendRow(child_item)
				self.build_tree(value, child_item)
			
				if isinstance(value, startrak.native.FileInfo):
						header_item = self.add_item(value.header, 'Header')
						child_item.appendRow(header_item)

	def data(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int= Qt.ItemDataRole.UserRole) -> QtCore.Any:
		if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
			item = self.itemFromIndex(index)
			return self.get_icon(item.data(Qt.ItemDataRole.UserRole))
		return super().data(index, role)
	
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			if section == 0:
					return "Element"
			elif section == 1:
					return "Type"
		return super().headerData(section, orientation, role)
	
	def get_icon(self, node : object):
		base_dir = 'startrak-ui/res/icons/'
		icons_path = { 'InspectionSession' : 'session.png',
							'ScanSession' : 'session.png',
							'Header' : 'header.png',
							'HeaderArchetype' : 'header.png',
							'FileList' : 'filelist.png',
							'StarList' : 'starlist.png'}
		if node is not None:
			icon_path = base_dir + icons_path.get(type(node).__name__, '')
			return QIcon(icon_path)
