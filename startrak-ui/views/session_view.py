from __future__ import annotations
from dataclasses import dataclass
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from typing import List, NamedTuple
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
from views.application import Application
from startrak.native.ext import STObject

class SessionTreeView(QtWidgets.QTreeView):
	def __init__(self, parent: QWidget | None = None) -> None:
		super().__init__(parent)
		app = Application.instance()
		app.on_sessionLoad.connect(self.setModel)
		self.setModel(app.st_module.get_session())
	
	def setModel(self, session):
		model = SessionTreeModel(session)
		super().setModel(model)
		self.expand(model.index(0, 0, QtCore.QModelIndex()))

	def updateItem(self, index, obj):
		item = index.internalPointer()
		if item:
			item.name = obj.name
			item.ref = obj
		self.model().dataChanged.emit(index, index)
		
_excluded = ['SessionLocationBlock']

class SessionTreeModel(QtCore.QAbstractItemModel):
	def __init__(self, session, parent: QtCore.QObject | None = None):
		super().__init__(parent)
		self.rootItem = SessionTreeModel.TreeItem(session.name, session, None, [])
		self.rootItem.grow_tree()
	
	@dataclass
	class TreeItem:
		name : str
		ref : STObject
		parent : SessionTreeModel.TreeItem | None
		children : List[SessionTreeModel.TreeItem]

		def grow_tree(self):
			export = [ (value.name if key.isdigit() else key.replace('_', ' ').capitalize(), value)
							for key, value in self.ref.__export__().items()
							if isinstance(value, STObject) and type(value).__name__ not in _excluded ]
			if len(export) == 0: return
			for name, value in export:
				node = SessionTreeModel.TreeItem(name, value, self, [])
				self.children.append(node)
				node.grow_tree()

		def type(self) -> str:
			return type(self.ref).__name__
		def __getitem__(self, index : int) -> _TreeItem:	#type: ignore
			if index == -1 and self.parent is not None:
				return self.parent
			return self.children[index]
	def rowCount(self, parent):
		if not parent.isValid():
			return 1
		node = parent.internalPointer()
		return len(node.children)
	def columnCount(self, parent): return 2
	def index(self, row, column, parent_index):
		if not self.hasIndex(row, column, parent_index):
			return QtCore.QModelIndex()

		if not parent_index.isValid():
			return self.createIndex(row, column, self.rootItem)
		else:
			parentItem = parent_index.internalPointer()

		childItem = parentItem[row]
		return self.createIndex(row, column, childItem)

	def parent(self, child_index):
		childItem = child_index.internalPointer()
		parentItem = childItem.parent

		if parentItem is None:
			return QtCore.QModelIndex()
		return self.createIndex(parentItem.children.index(childItem), 0, parentItem)

	def data(self, index, role):
		if not index.isValid():
			return None
		node = index.internalPointer()

		if role == Qt.DisplayRole:
			match index.column():
				case 0:
					return f'{node.name}'
				case 1:
					return f'{node.type()}'
				case _:
					return None
		elif role == Qt.DecorationRole and index.column() == 0:
			return self.get_icon(node)
		return None
	
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			if section == 0:
					return "Element"
			elif section == 1:
					return "Type"
		return super().headerData(section, orientation, role)
	def get_icon(self, node : TreeItem):
		base_dir = 'startrak-ui/res/icons/'
		icons_path = { 'InspectionSession' : 'session.png',
							'ScanSession' : 'session.png',
							'Header' : 'header.png',
							'HeaderArchetype' : 'header.png',
							'FileList' : 'filelist.png',
							'StarList' : 'starlist.png'}
		if node is not None:
			icon_path = base_dir + icons_path.get(node.type(), '')
			return QIcon(icon_path)
		