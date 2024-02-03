from qt.classes.range_slider import QRangeSlider
from typing import Optional
from PySide6 import QtWidgets
from PySide6.QtCore import Qt


class ImageViewer(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget) -> None:
		super().__init__(parent)
		self._view = QtWidgets.QGraphicsView(self)
		level_panel, level_slider = self.set_levels()

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self._view)
		layout.addWidget(level_panel)

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
		print(min_value, max_value)
