from typing import Any
import numpy as np
from qt.extensions import load_class, get_child
from qt.classes.range_slider import QRangeSlider
from PySide6 import QtWidgets, QtCore, QtGui

UI_ImageViewer, _ = load_class('image_viewer')
class ImageViewer(QtWidgets.QWidget, UI_ImageViewer):	#type:ignore
	view : QtWidgets.QGraphicsView
	level_slider : QRangeSlider
	current_file : Any | None

	def __init__(self, parent: QtWidgets.QWidget) -> None:
		QtWidgets.QWidget.__init__(self, parent)
		self.setupUi(self)

		self.view = get_child(self, 'graphicsView', QtWidgets.QGraphicsView)
		self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
		self.view.setScene(QtWidgets.QGraphicsScene())

		self.range_slider = get_child(self, 'level_slider', QRangeSlider)
		self.current_file = None
		self.view.scene().addText('Double click on a file to preview it').setDefaultTextColor(QtCore.Qt.GlobalColor.white)
	
	@QtCore.Slot(int, int)
	def on_levelChange(self, min_value, max_value):
		self.level_min = min_value / self.level_slider.maximum()
		self.level_max = max_value / self.level_slider.maximum()
		if self.current_file is not None:
			array = self.current_file.get_data()
			self.set_image(array)
	
	@QtCore.Slot(QtCore.QModelIndex)
	def on_itemSelected(self, index):
		pointer = index.internalPointer()
		if not pointer:
			return
		if type(pointer.ref).__name__ == 'FileInfo':
			self.current_file = pointer.ref
			if self.current_file is not None:
				array = self.current_file.get_data()
				self.set_image(array)

	def set_image(self, array):
		_m, _M = array.min(), array.max()
		_min, _max = _m + _M * self.level_min, _m + _M * self.level_max
		array = np.clip((array - _min) / (_max - _min) * 255, 0, 255).astype(np.uint8)
		scene = self.view.scene()
		scene.clear()
		qimage = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)
		
		pixmap = QtGui.QPixmap.fromImage(qimage)
		pixmap_item = scene.addPixmap(pixmap)
		pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
		scene.setSceneRect(QtCore.QRectF(pixmap.rect()))
		self.view.fitInView(pixmap_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

