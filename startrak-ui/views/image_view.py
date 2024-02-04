from typing import Any
import numpy as np
from qt.classes.range_slider import QRangeSlider
from PySide6 import QtWidgets, QtCore, QtGui


class ImageViewer(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget) -> None:
		super().__init__(parent)
		self.view = QtWidgets.QGraphicsView(self)
		self.scene = QtWidgets.QGraphicsScene()
		self.view.setScene(self.scene)
		self.view.setOptimizationFlags(QtWidgets.QGraphicsView.OptimizationFlag.IndirectPainting | QtWidgets.QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
		self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

		self.level_min = 0.
		self.level_max = 1.
		self.current_file : Any | None = None

		level_panel, self.level_slider = self.set_levels()
		self.level_slider.setMaximum(1000)
		layout = QtWidgets.QVBoxLayout(self)

		layout.addWidget(self.view)
		layout.addWidget(level_panel)

		self.scene.addText('Double click on a file to preview it').setDefaultTextColor(QtCore.Qt.GlobalColor.white)

	def set_levels(self):
		panel = QtWidgets.QFrame(self)
		panel.setObjectName('lvl_panel')
		label = QtWidgets.QLabel(panel)
		label.setText('Levels')
		slider = QRangeSlider(panel)
		slider.valueChanged.connect(self.on_levelChange)

		layout = QtWidgets.QVBoxLayout(panel)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(label)
		layout.addWidget(slider)

		return panel, slider
	
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
		self.scene.clear()
		qimage = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)
		
		pixmap = QtGui.QPixmap.fromImage(qimage)
		pixmap_item = self.scene.addPixmap(pixmap)
		pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
		self.scene.setSceneRect(QtCore.QRectF(pixmap.rect()))
		self.view.fitInView(pixmap_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

