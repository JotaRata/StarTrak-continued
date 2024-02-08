from __future__ import annotations
import enum
from typing import Callable
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
import numpy as np
from qt.extensions import load_class, get_child
from qt.classes.range_slider import QRangeSlider
from PySide6 import QtWidgets, QtCore, QtGui
from views.application import Application
from startrak.native import FileInfo, Star, StarList
from startrak.native.alias import ImageLike

UI_ImageViewer, _ = load_class('image_viewer')
class ImageViewer(QtWidgets.QWidget, UI_ImageViewer):	#type:ignore
	view : QtWidgets.QGraphicsView
	level_slider : QRangeSlider
	current_file : FileInfo | None
	current_index : QtCore.QModelIndex
	mapping_func : Callable[[ImageLike], ImageLike]
	star_labels : list[_StarLabelItem]
	on_starSelected = QtCore.Signal(QtCore.QModelIndex)

	def __init__(self, parent: QtWidgets.QWidget) -> None:
		QtWidgets.QWidget.__init__(self, parent)
		self.setupUi(self)

		self.view = get_child(self, 'graphicsView', QtWidgets.QGraphicsView)
		self.view.setScene(QtWidgets.QGraphicsScene())

		self.level_slider = get_child(self, 'level_slider', QRangeSlider)
		self.current_file = None
		self.view.scene().addText('Double click on a file to preview it').setDefaultTextColor(QtCore.Qt.GlobalColor.white)
		self.star_labels = []
		self.selected_star = -1
		self.on_levelChange(0, 255)
		self.on_colormapChange('linear')
	
	def update_image(self, index=None, obj=None):
		if not (obj is None or type(obj) is Star):
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
	def on_itemSelected(self, index):
		pointer = index.internalPointer()
		if not pointer:
			return
		if type(pointer.ref) is FileInfo:
			self.current_file = pointer.ref
			self.current_index = index
			self.update_image()

		elif type(pointer.ref) is Star:
			for i, item in enumerate(self.star_labels):
				item.selected = i == index.row()
				item.update()
				if item.selected:
					self.selected_star = i
	
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
		array = self.mapping_func(array)
		_min, _max = array.min() + array.max() * self.level_min, array.min() + array.max() * self.level_max
		array = np.clip((array - _min) / (_max - _min) * 255, 0, 255).astype(np.uint8)
		setup_itemColors(np.mean(array) > 128)

		scene = self.view.scene()
		scene.clear()
		qimage = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)
		pixmap = QtGui.QPixmap.fromImage(qimage)
		pixmap_item = scene.addPixmap(pixmap)
		pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
		scene.setSceneRect(QtCore.QRectF(pixmap.rect()))
		self.view.fitInView(pixmap_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
		self.draw_stars()

	def draw_stars(self,):
		session = Application.get_session()
		stars = session.included_stars
		scene = self.view.scene()
		self.star_labels.clear()

		def emit_starSelected(index):
				model = self.current_index.model()
				session_idx = model.index(0, 0, QtCore.QModelIndex())
				parent_idx = model.index(model.rowCount(session_idx) - 1, 0, session_idx)
				model_index = model.index(index, 0, parent_idx)
				self.selected_star = index
				
				for item in self.star_labels:
					if item.index == index:
						continue
					if item.selected:
						item.selected = False
						item.update()
				self.on_starSelected.emit(model_index)

		for i, star in enumerate(stars):
			item = _StarLabelItem(i, star)
			item.selected = self.selected_star == i
			# todo: Add method to StarList to retrieve indices by name
			item.on_mouseClick = emit_starSelected
			scene.addItem(item)
			self.star_labels.append(item)
	

class _StarLabelItem(QtWidgets.QGraphicsItem):
	def __init__(self, index : int, star : Star):
		super().__init__()
		self.index = index
		self.text = star.name
		self.position = star.position
		self.radius = star.aperture
		self.hovered = False
		self.selected = False
		self._bbox = QtCore.QRectF(0,0,0,0)
		self.on_mouseClick = None
		self.setAcceptHoverEvents(True)

	def boundingRect(self):
		return self._bbox

	def paint(self, painter, option, widget):
		scale = 1.0 / painter.transform().m22()
		color = highlighted_color if self.selected  else hover_color if self.hovered else normal_color
		alpha = 1 if self.hovered or self.selected else 0.5 if self.radius >= 8 else 0
		pad = 2 if self.hovered or self.selected else 0

		painter.setPen(QtGui.QPen(color, scale + 2))
		crect = QtCore.QRectF(self.position[0] - self.radius, self.position[1] - self.radius,
									2 * self.radius, 2 * self.radius).marginsAdded(QtCore.QMargins(pad, pad, pad, pad))
		painter.drawEllipse(crect)
		
		font = QtGui.QFont("Calibri", 10 * scale)
		painter.setFont(font)
		painter.setOpacity(alpha)
		rect = painter.boundingRect(crect, QtCore.Qt.AlignCenter, self.text)
		rect.translate(0, - self.radius - scale * 10)
		painter.drawText(rect, QtCore.Qt.AlignCenter, self.text)
		self._bbox = rect.united(crect)

	def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
		super().mouseDoubleClickEvent(event)
		self.selected = True
		if self.on_mouseClick:
			self.on_mouseClick(self.index)
		self.update()
	
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