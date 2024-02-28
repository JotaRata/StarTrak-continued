from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
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
		self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
	
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

	def add_item(self, obj : STObject | Any, parent : QStandardItem):
		result = self.model().add_item(obj, obj.name, parent)
		self.session_event('session_edit', result.index())()
		return result
	
	def removeRow(self, index : QModelIndex):
		result = self.model().removeRow(index.row(), index.parent())
		self.session_event('session_edit', index)()
		return result
		# s
	def expandParent(self, index : QtCore.QModelIndex):
		self.expand(index.parent())

	def mousePressEvent(self, event: QMouseEvent) -> None:
		super().mousePressEvent(event)
		index = self.currentIndex().siblingAtColumn(0)
		self.session_event('session_focus', index)()
	
	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		super().mouseDoubleClickEvent(event)
		index = self.currentIndex().siblingAtColumn(0)
		self.session_event('update_image', index)()
		
_excluded = ['SessionLocationBlock']
class SessionModel(QStandardItemModel):
	def __init__(self, session : startrak.native.Session):
		super().__init__()
		self._map = dict[object, QModelIndex]()
		self.rootItem = self.add_item(session, session.name, self)
		self.build_tree(session, self.rootItem)
		

	def get_index(self, obj : Any) -> QModelIndex:
		return self._map.get(obj, QModelIndex())

	def add_item(self, obj : Any, name : str = None, parent = None):
		item = QStandardItem()
		type_ = QStandardItem(type(obj).__name__)
		type_.setSelectable(False)
		if not name:
			name = type(obj).__name__
		item.setData(name, Qt.ItemDataRole.DisplayRole)
		item.setData(obj, Qt.ItemDataRole.UserRole)
		parent.appendRow((item, type_))
		return item
	
	def remove_item(self, obj : Any):
		index = self.get_index(obj)
		self.removeRow(index.row(), index.parent())
	
	def build_tree(self, item : startrak.native.ext.STObject, parent_item : QStandardItem):
		for key, value in item.__export__().items():
			if isinstance(value, STObject) and type(value).__name__ not in _excluded:
				if key.isdigit():
					key = value.name
				else:
					key = key.replace('_', ' ').capitalize()
				child_item = self.add_item(value, key, parent_item)
				self.build_tree(value, child_item)
			
				if isinstance(value, startrak.native.FileInfo):
						self.add_item(value.header, 'Header', child_item)

	def data(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int= Qt.ItemDataRole.UserRole) -> QtCore.Any:
		item = self.itemFromIndex(index)
		if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
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
