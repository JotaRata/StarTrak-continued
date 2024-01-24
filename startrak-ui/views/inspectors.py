
from __future__ import annotations
from abc import ABC
from typing import ClassVar, Optional
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt, Signal, Slot
from qt.extensions import *
from startrak.native import Position

class InspectorView(QtWidgets.QScrollArea):
	on_inspectorUpdate = Signal(QtCore.QModelIndex, object)

	def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)
		self.setWidgetResizable(True)
		self.content = QtWidgets.QWidget(self)
		self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		self.setWidget(self.content)
		self.lay = QtWidgets.QVBoxLayout(self.content)
		self.lay.setContentsMargins(0, 0, 0, 0)

		self.inspector : QtWidgets.QWidget | None = None

	@QtCore.Slot(QtCore.QModelIndex)
	def on_sesionViewUpdate(self, index):
		if self.inspector:
			self.inspector.destroy()
			self.lay.removeWidget( self.inspector)
		def emit_signal(value):
			self.on_inspectorUpdate.emit(index, value)

		pointer = index.internalPointer()
		if pointer is not None:
			ref = pointer.ref
			self.inspector = AbstractInspector.instantiate(type(ref).__name__, ref, self.content)
			self.inspector.on_change.connect(emit_signal)
			self.lay.addWidget(self.inspector)


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
	on_change = Signal(object)
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
	def __init__(self, value: object, parent: QtWidgets.QWidget) -> None:
		super().__init__(value, parent)
		name_field = get_child(self, 'nameField', QtWidgets.QLineEdit)
		contnet_field = get_child(self, 'contentField', QtWidgets.QTextEdit)

		name_field.setText(type(value).__name__)
		contnet_field.setText(str(value))

class StarInspector(AbstractInspector, ref_type= 'Star', layout_name= 'insp_star'): 
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

	@Slot(str)
	def name_changed(self, value):
		self.ref.name = value
		self.on_change.emit(self.ref)
	@Slot(int)
	def posx_changed(self, value):
		self.ref.position = Position(value, self.ref.position.y)
		self.on_change.emit(self.ref)
	@Slot(int)
	def posy_changed(self, value):
		self.ref.position = Position(self.ref.position.x, value)
		self.on_change.emit(self.ref)
	@Slot(int)
	def apert_changed(self, value):
		self.ref.aperture = value
		self.on_change.emit(self.ref)