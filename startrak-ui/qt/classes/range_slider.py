from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

class QRangeSlider(QtWidgets.QSlider):
	'''
		Based on https://gist.github.com/dridk/ff9c2e8dbf333fb6b808cf9873555045
	'''
	valueChanged = QtCore.Signal(int, int)
	def __init__(self, parent=None):
		super().__init__(parent)

		self.first_position = 1
		self.second_position = 8

		self.opt = QtWidgets.QStyleOptionSlider()
		self.opt.minimum = 0
		self.opt.maximum = 100

		self.setOrientation(QtCore.Qt.Orientation.Horizontal)

		self.setTickPosition(QtWidgets.QSlider.TicksAbove)
		self.setTickInterval(1)

		self.setSizePolicy(
			QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum,
										QtWidgets.QSizePolicy.ControlType.Slider)
		)

	def setRangeLimit(self, minimum: int, maximum: int):
		self.opt.minimum = minimum
		self.opt.maximum = maximum

	def setRange(self, start: int, end: int):
		self.first_position = start
		self.second_position = end

	def getRange(self):
		return (self.first_position, self.second_position)

	def setTickPosition(self, position: QtWidgets.QSlider.TickPosition):
		self.opt.tickPosition = position

	def setTickInterval(self, ti: int):
		self.opt.tickInterval = ti

	def paintEvent(self, event):

		painter = QtGui.QPainter(self)
		style = self.style()
		# Draw rule
		# self.opt.initFrom(self)
		# self.opt.rect = self.rect()
		# self.opt.sliderPosition = 0
		self.initStyleOption(self.opt)
		self.opt.subControls = QtWidgets.QStyle.SubControl.SC_SliderGroove | QtWidgets.QStyle.SubControl.SC_SliderTickmarks

		#   Draw GROOVE
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, painter, self)
		self.initStyleOption(self.opt)
		#  Draw INTERVAL
		color = self.palette().color(QtGui.QPalette.Highlight)
		color.setAlpha(160)
		painter.setBrush(QtGui.QBrush(color))
		painter.setPen(QtCore.Qt.NoPen)

		self.opt.sliderPosition = self.first_position
		x_left_handle = (
			style
			.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, QtWidgets.QStyle.SubControl.SC_SliderHandle)
			.right()
		)

		self.opt.sliderPosition = self.second_position
		x_right_handle = (
			style
			.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, QtWidgets.QStyle.SubControl.SC_SliderHandle)
			.left()
		)

		groove_rect = style.subControlRect(
			QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, QtWidgets.QStyle.SubControl.SC_SliderGroove, self
		)

		selection = QtCore.QRect(
			x_left_handle,
			groove_rect.y(),
			x_right_handle - x_left_handle,
			groove_rect.height(),
		).adjusted(-1, 1, 1, -1)
		painter.drawRect(selection)

		# Draw first handle
		self.initStyleOption(self.opt)
		self.opt.subControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
		self.opt.sliderPosition = self.first_position
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, painter)
		
		# Draw second handle
		self.initStyleOption(self.opt)
		self.opt.subControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
		self.opt.sliderPosition = self.second_position
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, painter)

	def mousePressEvent(self, event):
		self.opt.sliderPosition = self.first_position
		self._first_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, self.opt, event.pos()
		)

		self.opt.sliderPosition = self.second_position
		self._second_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, self.opt, event.pos()
		)

	def mouseMoveEvent(self, event):
		distance = self.opt.maximum - self.opt.minimum

		pos = self.style().sliderValueFromPosition(
			0, distance, event.pos().x(), self.rect().width()
		)

		if self._first_sc == QtWidgets.QStyle.SC_SliderHandle:
			if pos <= self.second_position:
					self.first_position = pos
					self.update()
					return
		if self._second_sc == QtWidgets.QStyle.SC_SliderHandle:
			if pos >= self.first_position:
					self.second_position = pos
					self.update()

	def update(self):
		super().update()
		self.valueChanged.emit(self.first_position, self.second_position)
		
	def sizeHint(self):
		SliderLength = 84
		TickSpace = 2

		w = SliderLength
		h = self.style().pixelMetric(QtWidgets.QStyle.PM_SliderThickness, self.opt, self)

		if (
			self.opt.tickPosition.value & QtWidgets.QSlider.TickPosition.TicksAbove.value
			or self.opt.tickPosition.value & QtWidgets.QSlider.TickPosition.TicksBelow.value
		):
			h += TickSpace

		return self.style().sizeFromContents(QtWidgets.QStyle.CT_Slider, self.opt, QtCore.QSize(w, h), self)
		