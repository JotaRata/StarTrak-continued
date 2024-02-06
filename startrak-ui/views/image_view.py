from typing import Callable
import numpy as np
from qt.extensions import load_class, get_child
from qt.classes.range_slider import QRangeSlider
from PySide6 import QtWidgets, QtCore, QtGui
from startrak.native import FileInfo
from startrak.native.alias import ImageLike

UI_ImageViewer, _ = load_class('image_viewer')
class ImageViewer(QtWidgets.QWidget, UI_ImageViewer):	#type:ignore
	view : QtWidgets.QGraphicsView
	level_slider : QRangeSlider
	current_file : FileInfo | None
	mapping_func : Callable[[ImageLike], ImageLike]

	def __init__(self, parent: QtWidgets.QWidget) -> None:
		QtWidgets.QWidget.__init__(self, parent)
		self.setupUi(self)

		self.view = get_child(self, 'graphicsView', QtWidgets.QGraphicsView)
		self.view.setScene(QtWidgets.QGraphicsScene())

		self.level_slider = get_child(self, 'level_slider', QRangeSlider)
		self.current_file = None
		self.view.scene().addText('Double click on a file to preview it').setDefaultTextColor(QtCore.Qt.GlobalColor.white)

		self.on_levelChange(0, 255)
		self.on_colormapChange('linear')
	
	@QtCore.Slot(int, int)
	def on_levelChange(self, min_value : int, max_value : int):
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
		if type(pointer.ref) is FileInfo:
			self.current_file = pointer.ref
			array = self.current_file.get_data()
			self.set_image(array)
	
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
		if self.current_file is not None:
				array = self.current_file.get_data()
				self.set_image(array)
			
	def set_image(self, array):
		array = self.mapping_func(array)
		_min, _max = array.min() + array.max() * self.level_min, array.min() + array.max() * self.level_max
		array = np.clip((array - _min) / (_max - _min) * 255, 0, 255).astype(np.uint8)

		scene = self.view.scene()
		scene.clear()
		qimage = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)
		
		pixmap = QtGui.QPixmap.fromImage(qimage)
		pixmap_item = scene.addPixmap(pixmap)
		pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
		scene.setSceneRect(QtCore.QRectF(pixmap.rect()))
		self.view.fitInView(pixmap_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

