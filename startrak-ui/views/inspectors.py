
from __future__ import annotations
from abc import ABC
import os
import re
from typing import ClassVar, Optional
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QEvent, QModelIndex, Qt, Signal, Slot
from PySide6.QtGui import QResizeEvent, QShowEvent
import numpy as np
from qt.extensions import *
from startrak.imageutils import sigma_stretch
from startrak.native import Position
from startrak.types.phot import _get_cropped
from views.application import Application

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
	prev_height = 0
	auto_exposure = False

	def __init__(self, star, index, parent: QtWidgets.QWidget) -> None:
		super().__init__(star, index, parent)
		self.draw_ready = False

		splitter = get_child(self, 'splitter', QtWidgets.QSplitter)
		name_field = get_child(self, 'nameField', QtWidgets.QLineEdit)
		posX_field = get_child(self, 'posXField', QtWidgets.QSpinBox)
		posY_field = get_child(self, 'posYField', QtWidgets.QSpinBox)
		apert_field = get_child(self, 'apertField', QtWidgets.QSpinBox)
		autoexp_check = get_child(self, 'auto_exp', QtWidgets.QCheckBox)

		name_field.setText(star.name)
		posX_field.setValue(star.position.x)
		posY_field.setValue(star.position.y)
		apert_field.setValue(star.aperture)
		autoexp_check.setChecked(StarInspector.auto_exposure)

		splitter.setSizes([StarInspector.prev_height, 1])

		phot_panel = get_child(self, 'phot_panel', QtWidgets.QFrame)
		flux_line = get_child(phot_panel, 'flux_line', QtWidgets.QLineEdit)
		background_line = get_child(phot_panel, 'background_line', QtWidgets.QLineEdit)
		flux_line.setText(f'{star.photometry.flux.value:.3f} ± {star.photometry.flux.sigma:.3f}')
		background_line.setText(f'{star.photometry.background.value:.3f} ± {star.photometry.background.sigma:.3f}')
		
		self.draw_ready = True
		self.draw_preview(star)

		def phot_click(event):
			index = self.index.model().index(0, 0, self.index)
			self.on_select.emit(index, True)
		phot_panel.mouseDoubleClickEvent = phot_click#type:ignore

	@Slot(str)
	def name_changed(self, value):
		self.ref.name = value
		self.on_change.emit(self.ref)
	@Slot(int)
	def posx_changed(self, value):
		self.ref.position = Position(value, self.ref.position.y)
		self.on_change.emit(self.ref)
		self.draw_preview(self.ref)
	@Slot(int)
	def posy_changed(self, value):
		self.ref.position = Position(self.ref.position.x, value)
		self.on_change.emit(self.ref)
		self.draw_preview(self.ref)
	@Slot(int)
	def apert_changed(self, value):
		self.ref.aperture = value
		self.on_change.emit(self.ref)
		self.draw_preview(self.ref)
	@Slot(bool)
	def set_autoexp(self, state):
		StarInspector.auto_exposure = state
		self.draw_preview(self.ref)
	@Slot(int, int)
	def splitter_changed(self, upper, lower):
		self.draw_ready = upper > 0
		if self.draw_ready and StarInspector.prev_height == 0:
			self.draw_preview(self.ref)
		self.showEvent(None)
		StarInspector.prev_height = upper

	#todo: Use reference file in session
	def draw_preview(self, star):
		if not self.draw_ready:	# avoid extra calls to this emthod when initializing
			return
		
		fileList = Application.get_session().included_files
		if not fileList or len(fileList) == 0:
			return
		circle_color = Application.instance().styleSheet().get_color('secondary')
		cross_color = Application.instance().styleSheet().get_color('primary')

		self.view = get_child(self, 'graphicsView', QtWidgets.QGraphicsView)
		self.view.setScene(QtWidgets.QGraphicsScene())
		scene = self.view.scene()
		scene.clear()

		orig_array = fileList[0].get_data()
		array = _get_cropped(orig_array, star.position, star.aperture * 2, 16)
		p1, p99 = np.nanpercentile(array if StarInspector.auto_exposure else orig_array, (0.1, 99.9))
		array = np.clip((array - p1) / (p99 - p1), 0, 1) * 255
		array = np.nan_to_num(array).astype(np.uint8)

		qimage = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)\
							.scaledToWidth(100)
		xcenter, ycenter = qimage.width()/2, qimage.height()/2
		scaled_apert = star.aperture * qimage.width() / array.shape[0]

		pixmap = QtGui.QPixmap.fromImage(qimage)
		scene.addPixmap(pixmap)
		scene.addEllipse(xcenter - scaled_apert, ycenter - scaled_apert, scaled_apert * 2, scaled_apert * 2
						,	circle_color)
		scene.addLine(xcenter, ycenter - 4, xcenter, ycenter + 4, cross_color)
		scene.addLine(xcenter - 4, ycenter, xcenter + 4, ycenter, cross_color)
		self.showEvent(None)
	
	def resizeEvent(self, event: QResizeEvent) -> None:
		super().resizeEvent(event)
		self.showEvent(None)
	def showEvent(self, event) -> None:
		if StarInspector.prev_height == 0:
			return
		self.view.fitInView(self.view.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

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

	def __init__(self, header, index, parent, readOnly= True, preview= False) -> None:
		super().__init__(header, index, parent)

		if not preview:
			file = HeaderInspector.HeaderEntry(self, 'File', os.path.basename(header.linked_file))
			self.layout().insertWidget(0, file)		#type:ignore

		header_panel = get_child(self, 'header_panel', QtWidgets.QFrame)
		for key, value in header.items():
			entry = HeaderInspector.HeaderEntry(header_panel, key, value, readOnly)
			header_panel.layout().addWidget(entry)

class HeaderArchetypeInspector(HeaderInspector, ref_type= 'HeaderArchetype', layout_name= 'insp_header'):
	def __init__(self, header, index, parent) -> None:
		super().__init__(header, index, parent, False)
		
		self.user_panel = QtWidgets.QFrame(self)
		self.user_panel.setObjectName('user_panel')
		user_panel = QtWidgets.QVBoxLayout(self.user_panel)
		user_label = QtWidgets.QLabel(self.user_panel)
		user_label.setText('User entries')
		user_panel.addWidget(user_label)

		self.layout().insertWidget(2, self.user_panel)	# type:ignore
		
		add_button = QtWidgets.QPushButton(self)
		add_button.setText('Add entry')
		self.layout().addWidget(add_button)

class FileInspector(AbstractInspector, ref_type= 'FileInfo', layout_name= 'insp_file'):
	def __init__(self, value, index, parent) -> None:
		super().__init__(value, index, parent)
		path_line = get_child(self, 'path_line', QtWidgets.QLineEdit)
		size_line = get_child(self, 'size_line', QtWidgets.QLineEdit)
		header_panel = get_child(self, 'header_panel', QtWidgets.QFrame)
		header_label = get_child(header_panel, 'header_label', QtWidgets.QLabel)

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
		header_panel.mouseDoubleClickEvent = header_click#type:ignore

class SessionInspector(AbstractInspector, ref_type= 'InspectionSession', layout_name= 'insp_session'):
	def __init__(self, value, index, parent) -> None:
		super().__init__(value, index, parent)
		properties_panel = get_child(self, 'properties_panel', QtWidgets.QFrame)
		validation_panel = get_child(self, 'validation_panel', QtWidgets.QFrame)
		included_panel = get_child(self, 'included_panel', QtWidgets.QFrame)

		self.set_propertiesPanel(value, properties_panel)
		self.set_validationPanel(value, validation_panel)
		self.set_includedPanel(value, included_panel)

	def set_propertiesPanel(self, value, frame):
		name_line = get_child(frame, 'name_line', QtWidgets.QLineEdit)
		cwd_line = get_child(frame, 'cwd_line', QtWidgets.QLineEdit)
		relPath_check = get_child(frame, 'relPath_check', QtWidgets.QCheckBox)

		name_line.setText(value.name)
		cwd_line.setText(value.working_dir)
		relPath_check.setChecked(value.relative_paths)
	
	def set_validationPanel(self, value, frame):
		strict_check = get_child(frame, 'strict_check', QtWidgets.QCheckBox)
		strict_check.setChecked(value.force_validation)

		def arch_panelBinder(event):
			index = self.index.model().index(0, 0, self.index)
			self.on_select.emit(index, True)

		arch_panel = get_child(frame, 'arch_panel', QtWidgets.QFrame)
		if value.archetype:
			archCount_label = get_child(arch_panel, 'archCount_label', QtWidgets.QLabel)
			archCount_label.setText(f'{len(value.archetype.keys())} entries')
			arch_panel.mouseDoubleClickEvent = arch_panelBinder#type:ignore
		else:
			arch_panel.setHidden(True)
		
	def set_includedPanel(self, value, frame):
		files_panel = get_child(frame, 'files_panel', QtWidgets.QFrame)
		stars_panel = get_child(frame, 'stars_panel', QtWidgets.QFrame)

		fileCount_label = get_child(frame, 'fileCount_label', QtWidgets.QLabel)
		starCount_label = get_child(frame, 'starCount_label', QtWidgets.QLabel)

		fileCount_label.setText(f'{len(value.included_files)} entries')
		starCount_label.setText(f'{len(value.included_stars)} entries')

		_rows = self.index.model().rowCount(self.index)
		def files_panelBinder(event):
			index = self.index.model().index(_rows - 2, 0, self.index)
			self.on_select.emit(index, True)
		def stars_panelBinder(event):
			index = self.index.model().index(_rows - 1, 0, self.index)
			self.on_select.emit(index, True)
		
		files_panel.mouseDoubleClickEvent = files_panelBinder#type:ignore
		stars_panel.mouseDoubleClickEvent = stars_panelBinder#type:ignore