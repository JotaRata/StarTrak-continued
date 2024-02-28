
from __future__ import annotations
from functools import partial
import re
from typing import Any
from PySide6.QtCore import QModelIndex, Slot
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QResizeEvent
import numpy as np
from qt.extensions import *

import startrak
import startrak.native.ext
from startrak.types.phot import _get_cropped
from views.application import Application
from views.abstract_inspectors import *


class InspectorView(QtWidgets.QFrame):
	inspector_event : UIEvent
	current_index : QtCore.QModelIndex

	def __init__(self, parent: QtWidgets.QWidget = None) -> None:
		super().__init__(parent)
		self.inspector_event = UIEvent(self)
		
		self.current_index = QtCore.QModelIndex()
		self.header_frame = QtWidgets.QFrame(self)
		header_layout = QtWidgets.QHBoxLayout(self.header_frame)
		header_layout.addStretch()
		header_layout.setContentsMargins(0, 0, 0, 0)
		self.inspector : QtWidgets.QWidget = None
	
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(2, 8, 2, 8)
		
		self.container = QtWidgets.QScrollArea(self)
		self.container.setWidgetResizable(True)
		self.container.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		content = QtWidgets.QFrame(self)
		self.container.setWidget(content)
		scroll_layout = QtWidgets.QVBoxLayout(content)
		scroll_layout.setContentsMargins(0, 0, 0, 0)

		layout.addWidget(self.header_frame)
		layout.addWidget(self.container)

	@QtCore.Slot(QtCore.QModelIndex)
	def create_inspector(self, index : QtCore.QModelIndex):
		self.destroy_inspector()
		ptr = get_data(index)
		if ptr is not None:
			self.current_index = index
			self.inspector = AbstractInspector.instantiate(ptr, index, self)
			if not self.inspector:
				self.inspector = AnyInspector(ptr, index, self)

			self.container.widget().layout().addWidget(self.inspector)
		self.setup_breadCrumbs(index)

	def redraw_inspector(self,):
		self.create_inspector(self.current_index)
	
	def destroy_inspector(self):
		if not self.inspector:
			return
		self.inspector.destroy()
		self.container.widget().layout().removeWidget( self.inspector)
	
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
			btn = QBreadCrumb(current_index)
			btn.clicked.connect(partial(self.create_inspector, current_index))
			if current_index == index:
				btn.setDisabled(True)
			else:
				if not parent.isValid():
					btn.setText('Session')
			layout.insertWidget(0, btn)
			current_index = parent
			count += 1
	
	def set_previewIndex(self, case : Literal['file', 'star'], index : QModelIndex):
		if case == 'file':
			FileListInspector.selected_row = index.row()
		if case == 'star':
			StarListInspector.selected_row = index.row()

class QBreadCrumb(QtWidgets.QPushButton):
	def __init__(self, index : QModelIndex):
		ptr = get_data(index)
		label = re.sub(r'([a-z])([A-Z])', r'\1 \2', type(ptr).__name__)
		super().__init__(label, None)

		name = getattr(ptr, 'name', None)
		self.setToolTip(type(ptr).__name__ + f': "{name}"' if name else '')

# -------------------- Inspectors -------------------------------------

class AnyInspector(AbstractInspector[Any], layout_name= 'insp_undef'):
	def __init__(self, value, index, parent: InspectorView):
		super().__init__(value, index, parent)
		content = get_child(self, 'contentField', QtWidgets.QTextEdit)
		content.setText(str(value))

class StarInspector(AbstractInspector[startrak.native.Star], layout_name= 'insp_star'): 
	prev_height = 0
	auto_exposure = False
	def __init__(self, value: startrak.native.Star, index: QModelIndex, parent: InspectorView):
		super().__init__(value, index, parent)
		self.draw_ready = False

		with self.inspector_event.blocked():
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
		self.inspector_event('update_image', (self.index))()

		phot_index = self.index.model().index(0, 0, self.index)
		phot_panel.mouseDoubleClickEvent = self.inspector_event('session_focus', phot_index)	#type:ignore

	@Slot(str)
	def name_changed(self, value):
		self.ref.name = value
		self.inspector_event('session_edit', self.index)()
	@Slot(int)
	def posx_changed(self, value):
		self.ref.position = startrak.native.Position(value, self.ref.position.y)
		self.inspector_event('session_edit', self.index)()
		self.draw_preview(self.ref)
	@Slot(int)
	def posy_changed(self, value):
		self.ref.position = startrak.native.Position(self.ref.position.x, value)
		self.inspector_event('session_edit', self.index)()
		self.draw_preview(self.ref)
	@Slot(int)
	def apert_changed(self, value):
		self.ref.aperture = value
		self.inspector_event('session_edit', self.index)()
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
	def __init__(self, value: startrak.native.PhotometryResult, index: QModelIndex, parent: InspectorView) -> None:
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


class HeaderInspector(AbstractHeaderInspector[startrak.native.Header]):
	pass

class HeaderArchetypeInspector(AbstractHeaderInspector[startrak.native.HeaderArchetype]):
	def __init__(self, value: startrak.native.HeaderArchetype, index: QModelIndex, parent: InspectorView) -> None:
		super().__init__(value, index, parent, readOnly= False)
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
	def __init__(self, value: startrak.native.FileInfo, index: QModelIndex, parent: InspectorView) -> None:
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

		header_index = self.index.model().index(0, 0, self.index)
		header_panel.mouseDoubleClickEvent = self.inspector_event('session_focus', header_index)	#type:ignore

class SessionInspector(AbstractInspector[startrak.sessionutils.InspectionSession], layout_name= 'insp_session'): #type: ignore
	def __init__(self, value: startrak.sessionutils.InspectionSession, index: QModelIndex, parent: InspectorView) -> None:
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

		arch_panel = get_child(frame, 'arch_panel', QtWidgets.QFrame)
		if value.archetype:
			archCount_label = get_child(arch_panel, 'archCount_label', QtWidgets.QLabel)
			archCount_label.setText(f'{len(value.archetype.keys())} entries')
			arch_index = self.index.model().index(0, 0, self.index)
			arch_panel.mouseDoubleClickEvent = self.inspector_event('session_focus', arch_index)#type:ignore
		else:
			arch_panel.setHidden(True)
		
	def set_includedPanel(self, value, frame):
		files_panel = get_child(frame, 'files_panel', QtWidgets.QFrame)
		stars_panel = get_child(frame, 'stars_panel', QtWidgets.QFrame)

		fileCount_label = get_child(frame, 'fileCount_label', QtWidgets.QLabel)
		starCount_label = get_child(frame, 'starCount_label', QtWidgets.QLabel)

		fileCount_label.setText(f'{len(value.included_files)} entries')
		starCount_label.setText(f'{len(value.included_stars)} entries')

		rows = self.index.model().rowCount(self.index)
		fileList_index = self.index.model().index(rows - 2, 0, self.index)
		starList_index = self.index.model().index(rows - 1, 0, self.index)

		files_panel.mouseDoubleClickEvent = self.inspector_event('session_focus', fileList_index)#type:ignore
		stars_panel.mouseDoubleClickEvent = self.inspector_event('session_focus', starList_index)#type:ignore


class FileListInspector(AbstractCollectionInspector[startrak.native.FileList]):
	def setup_widget(self, item: startrak.native.FileInfo, index: int):
		return item.name, item.size
	def on_itemSelect(self, index: QModelIndex):
		self.inspector_event('update_image', index)()
	
class StarListInspector(AbstractCollectionInspector[startrak.native.StarList]):
	def on_itemSelect(self, index: QModelIndex):
		self.inspector_event('update_image', index)()