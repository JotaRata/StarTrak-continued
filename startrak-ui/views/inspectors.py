
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
		name_field = get_child(self, 'nameField', QtWidgets.QLabel)
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

class PhotometryInspector(AbstractInspector, ref_type= 'PhotometryResult', layout_name= 'insp_phot'):
	def __init__(self, value, parent) -> None:
		super().__init__(value, parent)

		method_line = get_child(self, 'method_line', QtWidgets.QLineEdit)
		flux_line = get_child(self, 'flux_line', QtWidgets.QLineEdit)
		background_line = get_child(self, 'background_line', QtWidgets.QLineEdit)
		aradius_line = get_child(self, 'aradius_line', QtWidgets.QLineEdit)
		aoffset_line = get_child(self, 'aoffset_line', QtWidgets.QLineEdit)
		awidth_line = get_child(self, 'awidth_line', QtWidgets.QLineEdit)

		method_line.setText(value.method)
		flux_line.setText(f'{value.flux.value:.3f} ± {value.flux.sigma:.3f}')
		background_line.setText(f'{value.background.value:.3f} ± {value.background.sigma:.3f}')
		aradius_line.setText(str(value.aperture_info.radius))
		aoffset_line.setText(str(value.aperture_info.offset))
		awidth_line.setText(str(value.aperture_info.width))

class HeaderInspector(AbstractInspector, ref_type= 'Header', layout_name= 'insp_header'):
	class HeaderEntry(QtWidgets.QFrame):
		def __init__(self, parent, key, value, readOnly = True) -> None:
			super().__init__(parent)
			self.setObjectName(str(id(self))[:7] + '_frame')
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

	
	def __init__(self, header, parent, readOnly= True) -> None:
		super().__init__(header, parent)

		content_frame = get_child(self, 'content', QtWidgets.QFrame)
		file = HeaderInspector.HeaderEntry(content_frame, 'File', header.linked_file)
		content_frame.layout().insertWidget(0, file)		#type:ignore

		header_frame = get_child(self, 'header_frame', QtWidgets.QFrame)
		for key, value in header.items():
			entry = HeaderInspector.HeaderEntry(header_frame, key, value, readOnly)
			header_frame.layout().addWidget(entry)

class HeaderArchetypeInspector(HeaderInspector, ref_type= 'HeaderArchetype', layout_name= 'insp_header'):
	def __init__(self, header, parent) -> None:
		super().__init__(header, parent, False)
		label = get_child(self, 'type_label', QtWidgets.QLabel)
		label.setText('Header Archetype')

		content_frame = get_child(self, 'content', QtWidgets.QFrame)
		add_button = QtWidgets.QPushButton(self)
		add_button.setText('Add entry')
		content_frame.layout().addWidget(add_button)


