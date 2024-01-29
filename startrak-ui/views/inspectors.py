
from __future__ import annotations
from abc import ABC
import os
import re
from typing import ClassVar, Optional
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QEvent, QModelIndex, Qt, Signal, Slot
from qt.extensions import *
from startrak.native import Position

class InspectorView(QtWidgets.QFrame):
	on_inspectorUpdate = Signal(QtCore.QModelIndex, object)
	on_inspectorSelect = Signal(QtCore.QModelIndex)

	def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)
		self.type_label = QtWidgets.QLabel(self)
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(2, 8, 2, 8)
		
		self.scroll_area = QtWidgets.QScrollArea(self)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		content = QtWidgets.QFrame(self)
		self.scroll_area.setWidget(content)
		scroll_layout = QtWidgets.QVBoxLayout(content)
		scroll_layout.setContentsMargins(0, 0, 0, 0)

		layout.addWidget(self.type_label)
		layout.addWidget(self.scroll_area)
		self.inspector : QtWidgets.QWidget | None = None

		self.setStyleSheet('''
				QFrame[objectName $= "frame"]{
					background-color: rgba(255, 255, 255, 10);
					border-radius: 8px
				}
				QFrame[objectName ^= "frame_"]{
					background-color: transparent;
				}

				QLabel {
					background-color: transparent;
				}
							''')

	@QtCore.Slot(QtCore.QModelIndex)
	def on_sesionViewUpdate(self, index):
		if self.inspector:
			self.inspector.destroy()
			self.scroll_area.widget().layout().removeWidget( self.inspector)
		def emit_update(value):
			self.on_inspectorUpdate.emit(index, value)
		def emit_select(value, updateInsp):
			self.on_inspectorSelect.emit(value)
			if updateInsp:
				self.on_sesionViewUpdate(value)

		pointer = index.internalPointer()
		if pointer is not None:
			ref = pointer.ref
			_type = type(ref).__name__
			self.inspector = AbstractInspector.instantiate(_type, ref, index, self.scroll_area)
			self.inspector.on_change.connect(emit_update)
			self.inspector.on_select.connect(emit_select)
			self.scroll_area.widget().layout().addWidget(self.inspector)
			type_label = re.sub(r'([a-z])([A-Z])', r'\1 \2', _type)
			self.type_label.setText(type_label)
	
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
	index : QModelIndex
	on_change = Signal(object)
	on_select = Signal(QModelIndex, bool)
	def __init__(self, value, index, parent) -> None:
		if type(self) is AbstractInspector:
			raise TypeError('Cannot instantiate abstract class "AbstractInspector"')
		
		super().__init__(parent)
		self.setupUi()
		self.ref = value
		self.index = index

	def setupUi(self):
		super().setupUi(self)
	@staticmethod
	def instantiate(type_name : str, value : object, index: QModelIndex, parent : QtWidgets.QWidget) -> AbstractInspector:
		if type_name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[type_name][0](value, index, parent)
		return AnyInspector(value, index, parent)
	
	@staticmethod
	def get_layout(name : str):
		if name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[name][1]
		raise KeyError(name)

class AnyInspector(AbstractInspector, ref_type= 'Any', layout_name= 'insp_undef'):
	def __init__(self, value, index, parent: QtWidgets.QWidget) -> None:
		super().__init__(value, index, parent)
		content = get_child(self, 'contentField', QtWidgets.QTextEdit)
		content.setText(str(value))

class StarInspector(AbstractInspector, ref_type= 'Star', layout_name= 'insp_star'): 
	def __init__(self, star, index, parent: QtWidgets.QWidget) -> None:
		super().__init__(star, index, parent)

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
	def __init__(self, value, index, parent) -> None:
		super().__init__(value, index, parent)

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

	def __init__(self, header, index, parent, readOnly= True, preview= False) -> None:
		super().__init__(header, index, parent)

		if not preview:
			file = HeaderInspector.HeaderEntry(self, 'File', os.path.basename(header.linked_file))
			self.layout().insertWidget(0, file)		#type:ignore

		header_frame = get_child(self, 'header_frame', QtWidgets.QFrame)
		for key, value in header.items():
			entry = HeaderInspector.HeaderEntry(header_frame, key, value, readOnly)
			header_frame.layout().addWidget(entry)

class HeaderArchetypeInspector(HeaderInspector, ref_type= 'HeaderArchetype', layout_name= 'insp_header'):
	def __init__(self, header, index, parent) -> None:
		super().__init__(header, index, parent, False)
		
		self.user_frame = QtWidgets.QFrame(self)
		self.user_frame.setObjectName('user_frame')
		user_frame = QtWidgets.QVBoxLayout(self.user_frame)
		user_label = QtWidgets.QLabel(self.user_frame)
		user_label.setText('User entries')
		user_frame.addWidget(user_label)

		self.layout().insertWidget(2, self.user_frame)	# type:ignore
		
		add_button = QtWidgets.QPushButton(self)
		add_button.setText('Add entry')
		self.layout().addWidget(add_button)

class FileInspector(AbstractInspector, ref_type= 'FileInfo', layout_name= 'insp_file'):
	def __init__(self, value, index, parent) -> None:
		super().__init__(value, index, parent)
		path_line = get_child(self, 'path_line', QtWidgets.QLineEdit)
		size_line = get_child(self, 'size_line', QtWidgets.QLineEdit)
		header_frame = get_child(self, 'header_frame', QtWidgets.QFrame)
		header_label = get_child(header_frame, 'header_label', QtWidgets.QLabel)

		date_line = get_child(self, 'date_line', QtWidgets.QLineEdit)
		dimx_line = get_child(self, 'dimx_line', QtWidgets.QLineEdit)
		dimy_line = get_child(self, 'dimy_line', QtWidgets.QLineEdit)
		bitdepth_line = get_child(self, 'bitdepth_line', QtWidgets.QLineEdit)
		exptime_line = get_child(self, 'exptime_line', QtWidgets.QLineEdit)
		focal_line = get_child(self, 'focal_line', QtWidgets.QLineEdit)
		filter_line = get_child(self, 'filter_line', QtWidgets.QLineEdit)

		if value.bytes < 1024:
			size = f'{value.bytes} bytes'
		elif value.bytes < 1048576:
			size = f'{value.bytes/1024:.2f} KB'
		else:
			size = f'{value.bytes/1048576:.2f} MB'

		path_line.setText(value.path)
		size_line.setText(size)
		header_label.setText(f'{len(value.header.keys())} elements.')

		dimx_line.setText(value.header['NAXIS1', str])
		dimy_line.setText(value.header['NAXIS2', str])
		bitdepth_line.setText(value.header['BITPIX', str] + ' bytes')
		date_line.setText(value.header['DATE-OBS', str, 'NA'])
		exptime_line.setText(value.header['EXPTIME', str, 'NA'])
		focal_line.setText(value.header['FOCALLEN', str, 'NA'])
		filter_line.setText(value.header['FILTER', str, 'NA'])

		def header_click(event):
			index = self.index.model().index(0, 0, self.index)
			self.on_select.emit(index, True)
		header_frame.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
		header_frame.mouseDoubleClickEvent = header_click#type:ignore