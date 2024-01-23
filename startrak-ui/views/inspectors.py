
from __future__ import annotations
from abc import ABC
from typing import ClassVar, Optional
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt
from qt.extensions import *

class InspectorView(QtWidgets.QScrollArea):
	def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)
		self.setWidgetResizable(True)
		self.content = QtWidgets.QWidget(self)
		self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		self.setWidget(self.content)
		self.lay = QtWidgets.QVBoxLayout(self.content)
		self.lay.setContentsMargins(0, 0, 0, 0)

		self.current_inspector : QtWidgets.QWidget | None = None

	@QtCore.Slot(QtCore.QModelIndex)
	def on_sesionViewUpdate(self, index : QtCore.QModelIndex):
		pointer = index.internalPointer()
		if pointer is not None:
			self.inspect_obj(pointer.ref)	# type: ignore

	def inspect_obj(self, value):
		if self.current_inspector:
			self.lay.removeWidget( self.current_inspector)
			self.current_inspector.destroy()
		
		self.current_inspector = AbstractInspector.instantiate(type(value).__name__, value, self.content)
		self.lay.addWidget(self.current_inspector)

# -------------------- Inspectors -------------------------------------
class AbstractInspectorMeta(type(QtWidgets.QFrame)):	#type: ignore
	supported: dict[str, tuple[type['AbstractInspector'], str]] = {}
	def __new__(cls, name, bases, namespace, ref_type='', layout_name='', **kwargs):
		if name == 'AbstractInspector':
			klass = super().__new__(cls, name, bases, namespace)
			return klass
		
		UI_Layout, _ = load_class(layout_name)
		bases += (UI_Layout, )
		klass = super().__new__(cls, name, bases, namespace)
		klass.ref_type = ref_type
		klass.layout_name = layout_name

		AbstractInspectorMeta.supported[ref_type] = klass, layout_name
		return klass

class AbstractInspector(QtWidgets.QFrame, metaclass=AbstractInspectorMeta):
	ref: object
	def __init__(self, value : object, parent: QtWidgets.QWidget) -> None:
		if type(self) is AbstractInspector:
			raise TypeError('Cannot instantiate abstract class "AbstractInspector"')
		
		super().__init__(parent)
		self.setupUi()
		self.ref = value

	def setupUi(self):
		super().setupUi(self)
	@staticmethod
	def instantiate(type_name : str, value : object, parent : QtWidgets.QWidget) -> AbstractInspector:
		if type_name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[type_name][0](value, parent)
		return AnyInspector(value, parent)
	
	@staticmethod
	def get_layout(name : str):
		if name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[name][1]
		raise KeyError(name)

class AnyInspector(AbstractInspector, ref_type= 'Any', layout_name= 'insp_undef'):
	pass
class StarInspector(AbstractInspector, ref_type= 'Star', layout_name= 'insp_star'): 
	# on_nameChange = Signal(str)
	# on_posXChange = Signal(int)
	# on_posYChange = Signal(int)
	# on_apertureChange = Signal(int)

	def __init__(self, star, parent: QtWidgets.QWidget) -> None:
		super().__init__(star, parent)

		name_field = get_child(self, 'nameField', QtWidgets.QLineEdit)
		posX_field = get_child(self, 'posXField', QtWidgets.QSpinBox)
		posY_field = get_child(self, 'posYField', QtWidgets.QSpinBox)
		apert_field = get_child(self, 'apertField', QtWidgets.QSpinBox)
		label_phot = get_child(self, 'label_phot', QtWidgets.QLabel)

		name_field.setText(star.name)
		posX_field.setValue(star.position.x)
		posY_field.setValue(star.position.y)
		apert_field.setValue(star.aperture)

		label_phot.setText(star.photometry.__pprint__(0, 2) if star.photometry else '')