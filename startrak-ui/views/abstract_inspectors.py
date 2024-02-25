from __future__ import annotations
import os
from typing import Generic, TypeVar
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QEnterEvent, QMouseEvent
from qt.extensions import *
from startrak.internals.exceptions import InstantiationError

import startrak.native
import startrak.native.ext


_T = TypeVar('_T')
_TInspectorRef = TypeVar('_TInspectorRef')
_THeader = TypeVar('_THeader', bound= startrak.native.Header)
_TCollection = TypeVar('_TCollection', bound= startrak.native.ext.STCollection)

class AbstractInspectorMeta(type(QtWidgets.QFrame)):	#type: ignore
	supported: dict[str, tuple[type['AbstractInspector'], str]] = {}
	
	def __new__(cls, name, bases, namespace, layout_name= '', **kwargs):
		if name == "AbstractInspector":
			klass = super().__new__(cls, name, bases, namespace)
			return klass
		
		if not layout_name:
			for base in bases:
				layout_name = getattr(base, '__layout__', None)
		
		if layout_name:
			UI_Layout, _ = load_class(layout_name)
			bases += (UI_Layout, )
		klass = super().__new__(cls, name, bases, namespace)
		
		for base in klass.__orig_bases__:
			if hasattr(base, '__args__'):
				generic_type = base.__args__[0]
				break
		klass.__target__ = generic_type.__name__
		klass.__layout__ = layout_name

		AbstractInspectorMeta.supported[klass.__target__] = klass, klass.__layout__
		return klass


class AbstractInspector(QtWidgets.QFrame, Generic[_TInspectorRef], metaclass=AbstractInspectorMeta):
	ref: _TInspectorRef
	index : QtCore.QModelIndex

	def __init__(self, value : _TInspectorRef, index : QModelIndex, parent : QtWidgets.QWidget) -> None:
		if type(self) is AbstractInspector:
			raise TypeError('Cannot instantiate abstract class "AbstractInspector"')
		
		super().__init__(parent.container)#type:ignore
		self.setupUi()
		self.ref = value
		self.index = index
		self._view = parent
	@property
	def inspector_event(self):
		return self._view.inspector_event
	
	def setupUi(self):
		if self.__layout__:
			super().setupUi(self)

	@staticmethod
	def instantiate(obj : _TInspectorRef, index: QtCore.QModelIndex, parent : QtWidgets.QWidget) -> AbstractInspector[_TInspectorRef] | None:
		t_name = type(obj).__name__
		if t_name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[t_name][0](obj, index, parent)
		return None
	
	@staticmethod
	def get_layout(name : str):
		if name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[name][1]
		raise KeyError(name)


class AbstractHeaderInspector(AbstractInspector[_THeader], layout_name= 'insp_header'):
	def __init__(self, value: _THeader, index: QModelIndex, parent: QtWidgets.QWidget, readOnly= True) -> None:
		if type(self) is AbstractHeaderInspector:
			raise InstantiationError(self)
		
		super().__init__(value, index, parent)
		self.container = get_child(self, 'header_panel', QtWidgets.QFrame)
		
		self.draw_element('File', os.path.basename(value.linked_file))
		for key, entry in value.items():
			self.draw_element(key, entry, readOnly)
	
	class _HeaderEntry(QtWidgets.QFrame):
		def __init__(self, key : str, value : Any, readOnly : bool = True,  parent : QtWidgets.QWidget = None) -> None:
			super().__init__(parent)
			self.setObjectName(str(id(self))[:7] + '_panel')
			self.label = QtWidgets.QLabel(self)
			self.line = QtWidgets.QLineEdit(self)
			self.label.setText(key)
			self.label.setMinimumWidth(64)
			self.line.setText(str(value))
			if readOnly:
				self.line.setReadOnly(True)
			layout = QtWidgets.QHBoxLayout(self)
			layout.addWidget(self.label)
			layout.addWidget(self.line)
			
	def draw_element(self, key : str, value : Any, readOnly= True):
		entry = self._HeaderEntry(key, value, readOnly, self.container)
		self.container.layout().addWidget(entry)
		return entry


class AbstractCollectionInspector(AbstractInspector[_TCollection], layout_name= 'insp_collection'):
	def __init__(self, collection: _TCollection, index: QModelIndex, parent: QtWidgets.QWidget) -> None:
		if type(self) is AbstractCollectionInspector:
			raise InstantiationError(self)
		super().__init__(collection, index, parent)
		name_label = get_child(self, 'name_label', QtWidgets.QLabel)
		info_label = get_child(self, 'info_label', QtWidgets.QLabel)
		self.list = get_child(self, 'listWidget', QtWidgets.QListWidget)
		name_label.setText(type(collection).__name__)
		info_label.setText(f'{len(collection)} elements.')
		for i, item in enumerate(collection):
			self.add_item(item, i)

	def add_item(self, item : Any, index : int) -> QtWidgets.QListWidgetItem:
		text = getattr(item, 'name', 'Item ' + str(index))
		item_wdg = QtWidgets.QListWidgetItem()
		wdg = self.create_widget(item, index)
		item_wdg.setSizeHint(wdg.sizeHint())
		self.list.addItem(item_wdg)
		self.list.setItemWidget(item_wdg, wdg)
		return item_wdg
	def create_widget(self, item : Any, index : int) -> AbstractCollectionInspector.ListItem:
		text, desc = self.setup_widget(item, index)
		wdg = AbstractCollectionInspector.ListItem(self, index, text, desc)
		return wdg
	def setup_widget(self, item : Any, index : int) -> tuple[str, str]:
		return getattr(item, 'name', 'Item ' + str(index)),  type(item).__name__
	
	class ListItem(QtWidgets.QWidget):
		def __init__(self, parent : AbstractCollectionInspector, index : int, text : str, desc : str):
			super().__init__()
			model = parent.index.model()
			self._layout = QtWidgets.QGridLayout(self)
			self.name_label = QtWidgets.QLabel(text, self)
			self.desc_label = QtWidgets.QLabel(desc, self)
			self.del_btn = QtWidgets.QPushButton(self)
			self.del_btn.setObjectName('remove-button')
			self._layout.addWidget(self.name_label, 0, 0)
			self._layout.addWidget(self.desc_label, 1, 0)
			self.del_btn.setSizePolicy( *(QtWidgets.QSizePolicy.Policy.Fixed,)*2)
			self.del_btn.setFixedSize(16, 16)
			self.del_btn.hide()

			self._layout.addWidget(self.del_btn, 0, 1)
			self.index = model.index(index, 0, parent.index)
			self.mouseDoubleClickEvent = parent.inspector_event('session_focus', self.index)#type: ignore

			sp_retain = self.del_btn.sizePolicy()
			sp_retain.setRetainSizeWhenHidden(True)
			self.del_btn.setSizePolicy(sp_retain)

		def layout(self) -> QtWidgets.QGridLayout:
			return self._layout
		def enterEvent(self, event: QEnterEvent) -> None:
			super().enterEvent(event)
			self.del_btn.show()
		def leaveEvent(self, event: QtCore.QEvent) -> None:
			super().leaveEvent(event)
			self.del_btn.hide()