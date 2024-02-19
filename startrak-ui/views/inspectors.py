
from __future__ import annotations
from functools import partial
import os
import re
from typing import Any, Generic
from PySide6.QtCore import QModelIndex, Signal, Slot
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QMouseEvent, QResizeEvent
import numpy as np
from qt.extensions import *

import startrak
from startrak.internals.exceptions import InstantiationError
from startrak.types.phot import _get_cropped
from views.application import Application

class InspectorView(QtWidgets.QFrame):
	on_inspectorUpdate = Signal(QtCore.QModelIndex, object)
	on_inspectorSelect = Signal(QtCore.QModelIndex)
	current_index : QtCore.QModelIndex

	def __init__(self, parent: QtWidgets.QWidget = None) -> None:
		super().__init__(parent)
		
		self.current_index = QtCore.QModelIndex()
		self.header_frame = QtWidgets.QFrame(self)
		header_layout = QtWidgets.QHBoxLayout(self.header_frame)
		header_layout.addStretch()
		header_layout.setContentsMargins(0, 0, 0, 0)
	
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(2, 8, 2, 8)
		
		self.scroll_area = QtWidgets.QScrollArea(self)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		content = QtWidgets.QFrame(self)
		self.scroll_area.setWidget(content)
		scroll_layout = QtWidgets.QVBoxLayout(content)
		scroll_layout.setContentsMargins(0, 0, 0, 0)

		layout.addWidget(self.header_frame)
		layout.addWidget(self.scroll_area)
		self.inspector : QtWidgets.QWidget | None = None

	@QtCore.Slot(QtCore.QModelIndex)
	def on_sesionViewUpdate(self, index : QtCore.QModelIndex):
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
			self.current_index = index
			self.inspector = AbstractInspector.instantiate(type(pointer.ref).__name__, pointer.ref, index, self.scroll_area)
			self.inspector.on_change.connect(emit_update)
			self.inspector.on_select.connect(emit_select)
			self.scroll_area.widget().layout().addWidget(self.inspector)
		self.setup_breadCrumbs(index)
	
	def setup_breadCrumbs(self, index : QtCore.QModelIndex):
		layout = cast(QtWidgets.QHBoxLayout, self.header_frame.layout())
		for i in reversed(range(layout.count())): 
			wdg = layout.itemAt(i).widget()
			if wdg:
				wdg.deleteLater()

		count = 1
		current_index = index
		while current_index.isValid():
			if count > 4:
				break
			parent = current_index.parent()
			
			# type_label = ' ' + type(current_index.internalPointer().ref).__name__ + ' '
			btn = QBreadCrumb(current_index, self.header_frame)
			btn.clicked.connect(partial(self.on_sesionViewUpdate, current_index))
			if current_index == index:
				btn.setDisabled(True)
			else:
				if not parent.isValid():
					btn.setText('Session')
			layout.insertWidget(0, btn)
			current_index = parent
			count += 1

class QBreadCrumb(QtWidgets.QPushButton):
	def __init__(self, index, parent):
		ref = index.internalPointer().ref
		label = re.sub(r'([a-z])([A-Z])', r'\1 \2', type(ref).__name__)
		super().__init__(label, None)

		name = getattr(ref, 'name', None)
		self.setToolTip(type(ref).__name__ + f': "{name}"' if name else '')

# -------------------- Inspectors -------------------------------------
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

TInspectorRef = TypeVar('TInspectorRef')
class AbstractInspector(QtWidgets.QFrame, Generic[TInspectorRef], metaclass=AbstractInspectorMeta):
	ref: TInspectorRef
	index : QtCore.QModelIndex
	on_change = Signal(object)
	on_select = Signal(QtCore.QModelIndex, bool)

	def __init__(self, value : TInspectorRef, index : QModelIndex, parent : QtWidgets.QWidget = None) -> None:
		if type(self) is AbstractInspector:
			raise TypeError('Cannot instantiate abstract class "AbstractInspector"')
		
		super().__init__(parent)
		self.setupUi()
		self.ref = value
		self.index = index

	def setupUi(self):
		if not self.__layout__:
			return
		super().setupUi(self)

	@staticmethod
	def instantiate(type_name : str, value : TInspectorRef, index: QtCore.QModelIndex, parent : QtWidgets.QWidget) -> AbstractInspector:
		if type_name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[type_name][0](value, index, parent)
		return AnyInspector(value, index, parent)
	
	@staticmethod
	def get_layout(name : str):
		if name in AbstractInspectorMeta.supported:
			return AbstractInspectorMeta.supported[name][1]
		raise KeyError(name)

class AnyInspector(AbstractInspector[Any], layout_name= 'insp_undef'):
	def __init__(self, value, index, parent: QtWidgets.QWidget) -> None:
		super().__init__(value, index, parent)
		content = get_child(self, 'contentField', QtWidgets.QTextEdit)
		content.setText(str(value))

class StarInspector(AbstractInspector[startrak.native.Star], layout_name= 'insp_star'): 
	prev_height = 0
	auto_exposure = False
	def __init__(self, value: startrak.native.Star, index: QModelIndex, parent: QtWidgets.QWidget = None) -> None:
		super().__init__(value, index, parent)
		self.draw_ready = False

		splitter = get_child(self, 'splitter', QtWidgets.QSplitter)
		name_field = get_child(self, 'nameField', QtWidgets.QLineEdit)
		posX_field = get_child(self, 'posXField', QtWidgets.QSpinBox)
		posY_field = get_child(self, 'posYField', QtWidgets.QSpinBox)
		apert_field = get_child(self, 'apertField', QtWidgets.QSpinBox)
		autoexp_check = get_child(self, 'auto_exp', QtWidgets.QCheckBox)

		name_field.setText(value.name)
		posX_field.setValue( int(value.position.x))
		posY_field.setValue( int(value.position.y))
		apert_field.setValue(value.aperture)
		autoexp_check.setChecked(StarInspector.auto_exposure)

		splitter.setSizes([StarInspector.prev_height, 1])

		phot_panel = get_child(self, 'phot_panel', QtWidgets.QFrame)
		flux_line = get_child(phot_panel, 'flux_line', QtWidgets.QLineEdit)
		background_line = get_child(phot_panel, 'background_line', QtWidgets.QLineEdit)
		flux_line.setText(f'{value.photometry.flux.value:.3f} ± {value.photometry.flux.sigma:.3f}')
		background_line.setText(f'{value.photometry.background.value:.3f} ± {value.photometry.background.sigma:.3f}')
		
		self.draw_ready = True
		self.draw_preview(value)

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
		self.ref.position = startrak.native.Position(value, self.ref.position.y)
		self.on_change.emit(self.ref)
		self.draw_preview(self.ref)
	@Slot(int)
	def posy_changed(self, value):
		self.ref.position = startrak.native.Position(self.ref.position.x, value)
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

class PhotometryInspector(AbstractInspector[startrak.native.PhotometryResult], layout_name= 'insp_phot'):
	def __init__(self, value: startrak.native.PhotometryResult, index: QModelIndex, parent: QtWidgets.QWidget = None) -> None:
		super().__init__(value, index, parent)
		aperture = value.aperture_info
		flux_area = f"{np.pi * aperture.radius ** 2:.2f}"
		get_child(self, 'method_line', QtWidgets.QLineEdit).setText(value.method)
		get_child(self, 'flux_int', QtWidgets.QLineEdit).setText(f"{value.flux.value:.2f}")
		get_child(self, 'flux_area', QtWidgets.QLineEdit).setText(flux_area)
		get_child(self, 'flux_sigma', QtWidgets.QLineEdit).setText(f"{value.flux.sigma:.2f}")
		get_child(self, 'flux_max', QtWidgets.QLineEdit).setText(f"{value.flux.max:.2f}")
		get_child(self, 'flux_raw', QtWidgets.QLineEdit).setText(f"{value.flux.raw:.2f}")

		bkg_area = f"{np.pi * (2*(aperture.radius+aperture.offset) * aperture.width + aperture.width**2):.2f}"
		get_child(self, 'bkg_int', QtWidgets.QLineEdit).setText(f"{value.background.value:.2f}")
		get_child(self, 'bkg_area', QtWidgets.QLineEdit).setText(bkg_area)
		get_child(self, 'bkg_sigma', QtWidgets.QLineEdit).setText(f"{value.background.sigma:.2f}")
		get_child(self, 'bkg_max', QtWidgets.QLineEdit).setText(f"{value.background.max:.2f}")

		# todo: Replace with per-Photometry method properties
		get_child(self, 'aoffset_line', QtWidgets.QLineEdit).setText(f"{aperture.offset:.2f} px")
		get_child(self, 'aradius_line', QtWidgets.QLineEdit).setText(f"{aperture.radius:.2f} px")
		get_child(self, 'awidth_line', QtWidgets.QLineEdit).setText(f"{aperture.width:.2f} px")


_THeader = TypeVar('_THeader', bound= startrak.native.Header)
class AbstractHeaderInspector(AbstractInspector[_THeader], layout_name= 'insp_header'):
	def __init__(self, value: _THeader, index: QModelIndex, readOnly= True, parent: QtWidgets.QWidget = None) -> None:
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

class HeaderInspector(AbstractHeaderInspector[startrak.native.Header]):
	pass

class HeaderArchetypeInspector(AbstractHeaderInspector[startrak.native.HeaderArchetype]):
	def __init__(self, value: startrak.native.HeaderArchetype, index: QModelIndex, parent: QtWidgets.QWidget = None) -> None:
		super().__init__(value, index, False, parent)
		self.user_panel = QtWidgets.QFrame(self)
		self.user_panel.setObjectName('user_panel')
		user_panel = QtWidgets.QVBoxLayout(self.user_panel)
		user_label = QtWidgets.QLabel(self.user_panel)
		user_label.setText('User entries')
		user_panel.addWidget(user_label)
		self.layout().insertWidget(1, self.user_panel)	# type:ignore
		
		add_button = QtWidgets.QPushButton(self)
		add_button.setText('Add entry')
		self.layout().addWidget(add_button)


class FileInspector(AbstractInspector[startrak.native.FileInfo], layout_name= 'insp_file'):
	def __init__(self, value: startrak.native.FileInfo, index: QModelIndex, parent: QtWidgets.QWidget = None) -> None:
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

class SessionInspector(AbstractInspector[startrak.sessionutils.InspectionSession], layout_name= 'insp_session'): #type: ignore
	def __init__(self, value: startrak.sessionutils.InspectionSession, index: QModelIndex, parent: QtWidgets.QWidget = None) -> None:
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

_TCollection = TypeVar('_TCollection', bound= startrak.native.ext.STCollection)
class AbstractCollectionInspector(AbstractInspector[_TCollection]):
	def __init__(self, value: _TCollection, index: QModelIndex, parent: QtWidgets.QWidget = None) -> None:
		super().__init__(value, index, parent)
		layout= QtWidgets.QVBoxLayout(self)
		layout.addWidget(QtWidgets.QLabel(f'{type(value).__name__}: {len(value)} elements'))
		
		for i in range(len(value)):
			entry= self.create_element(i)
			self.layout().addWidget(entry)
		layout.addStretch()

	class _CollectionEntry(QtWidgets.QFrame):
		def __init__(self, label: str, description: str= '', parent: QtWidgets.QWidget = None):
			super().__init__(parent)
			self.setObjectName(str(id(self))[:7] + '_panel')
			self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
			layout = QtWidgets.QVBoxLayout(self)
			self.name_label = QtWidgets.QLabel(label, self)
			self.desc_label = QtWidgets.QLabel(description, self)
			layout.addWidget(self.name_label)
			layout.addWidget(self.desc_label)
	
	def _create_entry(self, index: int, label= 'Element', desc= ''):
		'''Internal function, Do not override'''
		model = self.index.model()
		child_idx = model.index(index, 0, self.index)
		entry= AbstractCollectionInspector._CollectionEntry(label, desc, parent= self)
		def click_binder(event):
				self.on_select.emit(child_idx, True)
		entry.mouseDoubleClickEvent = click_binder 	#type: ignore
		return entry
			
	def create_element(self, index : int):
		match index:
			case 1: _th = 'st'
			case 2: _th = 'nd'
			case 3: _th = 'rd'
			case _: _th = 'th'
		entry = self._create_entry(index, f'{index}{_th} Element')
		return entry

class FileListInspector(AbstractCollectionInspector[startrak.native.FileList]):
	def create_element(self, index: int):
		ref = self.ref[index]
		entry= self._create_entry(index, f'File: {ref.name}', f'Size: {ref.size}')
		return entry