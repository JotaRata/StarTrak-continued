from __future__ import annotations
from typing import Any, List, NamedTuple
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt
from PySide6.QtGui import QIcon
from startrak.native import Session
from startrak.native.ext import STObject

_excluded = ['SessionLocationBlock']
class _TreeItem(NamedTuple):
	name : str
	ref : STObject
	parent : _TreeItem | None
	children : List[_TreeItem]

	def add_child(self, node : _TreeItem):
		self.children.append(node)
		
	def grow_tree(self):
		export = list[tuple[str, Any]]()
		for key, value in self.ref.__export__().items():
			if not isinstance(value, STObject):
				continue
			if type(value).__name__ in _excluded:
				continue

			if key.isdigit():
				name = value.name
			else:
				name = key.replace('_', ' ').capitalize()

			export.append((name, value))

		if len(export) == 0:
			return
		for name, value in export:
			node = _TreeItem(name, value, self, [])
			self.add_child(node)
			node.grow_tree()

	def type(self) -> str:
		return type(self.ref).__name__
	
	def __getitem__(self, index : int) -> _TreeItem:	#type: ignore
		if index == -1 and self.parent is not None:
			return self.parent
		return self.children[index]
	def __len__(self) -> int:
		return len(self.children)
	def __repr__(self) -> str:
		return f'{self.type()}: "{self.name}"'


class SessionTreeModel(QAbstractItemModel):
	def __init__(self, session : Session, parent: QObject | None = None):
		super().__init__(parent)
		self.rootItem = _TreeItem(session.name, session, None, [])
		self.rootItem.grow_tree()

	def rowCount(self, parent):
		if not parent.isValid():
			# Root item, return the number of root children
			return 1
		node = parent.internalPointer()
		return len(node)

	def columnCount(self, parent):
		return 2  # Two columns for demonstration purposes
	
	def index(self, row, column, parent_index):
		if not self.hasIndex(row, column, parent_index):
			return QModelIndex()

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
			return QModelIndex()
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
	
	def get_icon(self, node : _TreeItem):
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