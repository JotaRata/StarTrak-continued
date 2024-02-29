from __future__ import annotations
import enum
from typing import Any, Callable
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QWidget
import numpy as np
from qt.extensions import *
from qt.classes.range_slider import QRangeSlider
from PySide6 import QtWidgets, QtCore, QtGui
from startrak.types.phot import _get_cropped
from views.application import Application
from startrak.native import FileInfo, Star, StarList
from startrak.native.alias import ImageLike

normal_color =  None
hover_color =  None
selected_color =  None
highlighted_color =  None

UI_ImageViewer, _ = load_class('image_viewer')
class ImageViewer(QtWidgets.QWidget, UI_ImageViewer):	#type:ignore
	view : QtWidgets.QGraphicsView
	level_slider : QRangeSlider
	current_file : FileInfo | None
	current_index : QtCore.QModelIndex
	mapping_func : Callable[[ImageLike], ImageLike]
	star_labels : list[_StarLabelItem]

	viewer_event : UIEvent

	def __init__(self, parent: QtWidgets.QWidget) -> None:
		super().__init__(parent)
		self.setupUi(self)
		self.viewer_event = UIEvent(self)

		self.view = get_child(self, 'graphicsView', QtWidgets.QGraphicsView)
		self.view.setScene(QtWidgets.QGraphicsScene())
		self.level_slider = get_child(self, 'level_slider', QRangeSlider)
		combo_box = get_child(self, 'comboBox', QtWidgets.QComboBox)
		self.current_file = None
		self.current_index = QtCore.QModelIndex()
		self.view.scene().addText('Double click on a file to preview it').setDefaultTextColor(QtCore.Qt.GlobalColor.white)
		self.star_labels = []
		self.selected_star = -1
		self.level_slider.setRange(0, 125)
		combo_box.setCurrentIndex(1)
		# self.on_levelChange(0, 100)
		# self.on_colormapChange('logarithmic')
	
	def update_image(self, index : QtCore.QModelIndex = None):
		if not index:
			index = self.current_index
		if not index.isValid():
			return
		
		if self.current_file is not None:
			array = self.current_file.get_data()
			self.set_image(array)

	@QtCore.Slot(int, int)
	def on_levelChange(self, min_value : int, max_value : int):
		self.level_min = min_value / self.level_slider.maximum()
		self.level_max = max_value / self.level_slider.maximum()
		self.update_image()
	
	@QtCore.Slot(QtCore.QModelIndex)
	def view_file(self, index):
		pointer = get_data(index)
		if not pointer:
			return
		if type(pointer) is FileInfo:
			self.current_file = pointer
			self.current_index = index
			self.update_image()

		elif type(pointer) is Star:
			for i, item in enumerate(self.star_labels):
				item.selected = i == index.row()
				item.update()
				if item.selected:
					self.selected_star = i

	def redraw_viewer(self):
		if not self.current_index.isValid():
			return
		index = self.current_index.model().get_index(self.current_file)
		self.view_file(index)
	
	@QtCore.Slot(str)
	def on_colormapChange(self, value : str):
		match value.lower():
			case 'linear':
				self.mapping_func = lambda x: x
			case 'logarithmic':
				self.mapping_func = lambda x: np.log10(x)
			case 'negative linear':
				self.mapping_func = lambda x: np.max(x) - x
			case _:
				raise KeyError(value)
		self.update_image()
			
	def set_image(self, array):
		array = array[0:-1, 0:-1].copy()
		array = self.mapping_func(array)
		_min, _max = array.min() + array.max() * self.level_min, array.min() + array.max() * self.level_max
		array = np.clip((array - _min) / (_max - _min) * 255, 0, 255)
		array = np.nan_to_num(array).astype(np.uint8)
		setup_itemColors(np.mean(array) > 128)

		scene = self.view.scene()
		scene.clear()
		qimage = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)\
							.scaledToWidth(1024)
		pixmap = QtGui.QPixmap.fromImage(qimage)
		scene.addPixmap(pixmap)
		# pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
		self.showEvent(None)
		self.draw_stars()
	def showEvent(self, event) -> None:
		self.view.fitInView(self.view.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

	def draw_stars(self,):
		session = Application.get_session()
		stars = session.included_stars
		self.star_labels.clear()

		model = self.current_index.model()
		session_idx = model.index(0, 0, QtCore.QModelIndex())
		parent_idx = model.index(model.rowCount(session_idx) - 1, 0, session_idx)

		for i, star in enumerate(stars):
			star_index = model.index(i, 0, parent_idx)
			item = ImageViewer._StarLabelItem(star_index, star, self)
			item.selected = self.selected_star == i
			self.view.scene().addItem(item)
			self.star_labels.append(item)
		
	def set_selectedStar(self, index : QtCore.QModelIndex):
		self.selected_star = index.row()
		for item in self.star_labels:
			if item.index == index:
				continue
			if item.selected:
				item.selected = False
				item.update()

	class _StarLabelItem(QtWidgets.QGraphicsItem):
		def __init__(self, index : QtCore.QModelIndex, star : Star, parent: ImageViewer):
			super().__init__()
			self.index = index
			self.star = star
			self.parent = parent
			
			self.hovered = False
			self.selected = False
			self._bbox = QtCore.QRectF(0,0,0,0)
			self.on_mouseClick = None
			self.setAcceptHoverEvents(True)

		def boundingRect(self) -> QtCore.QRectF:
			return self._bbox

		def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QWidget = None):
			global normal_color, hover_color, selected_color, highlighted_color
			scale = 1.0 / painter.transform().m22()
			
			color = highlighted_color if self.selected  else hover_color if self.hovered else normal_color
			alpha = 1 if self.hovered or self.selected else 0.5 if self.star.aperture >= 8 else 0
			pad = 2 if self.hovered or self.selected else 0

			painter.setPen(QtGui.QPen(color, scale + 2))
			crect = QtCore.QRectF(self.star.position[0] - self.star.aperture, self.star.position[1] - self.star.aperture,
										2 * self.star.aperture, 2 * self.star.aperture).marginsAdded(QtCore.QMargins(pad, pad, pad, pad))
			painter.drawEllipse(crect)
			
			font = QtGui.QFont("Calibri", 10 * int(scale))
			painter.setFont(font)
			painter.setOpacity(alpha)
			rect = painter.boundingRect(crect, QtCore.Qt.AlignmentFlag.AlignCenter, self.star.name)
			rect.translate(0, - self.star.aperture - scale * 10)
			painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.star.name)
			self._bbox = rect.united(crect)

		def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
			if self.selected:
				return
			# super().mouseDoubleClickEvent(event)
			self.selected = True
			self.update()
			self.parent.set_selectedStar(self.index)
			self.parent.viewer_event('session_focus', self.index)()
		
		def hoverEnterEvent(self, event):
			super().hoverEnterEvent(event)
			self.hovered = True
			self.update()

		def hoverLeaveEvent(self, event):
			super().hoverLeaveEvent(event)
			self.hovered = False
			self.update()

def setup_itemColors(inverted):
	global normal_color, hover_color, selected_color, highlighted_color
	normal_color = Application.instance().styleSheet().get_color('secondary')
	if inverted:
		hover_color = Application.instance().styleSheet().get_color('secondary-dark')
		selected_color = Application.instance().styleSheet().get_color('secondary-dark')
		highlighted_color = Application.instance().styleSheet().get_color('highlighted-dark')
	else:
		hover_color = Application.instance().styleSheet().get_color('secondary-light')
		selected_color = Application.instance().styleSheet().get_color('secondary-light')
		highlighted_color = Application.instance().styleSheet().get_color('highlighted')