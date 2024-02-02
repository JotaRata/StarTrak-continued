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

		self.press_state = -1
		self.hover_state = -1

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
			.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
			.right()
		)
		self.opt.sliderPosition = self.second_position
		x_right_handle = (
			style
			.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
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

		def_state = QtWidgets.QStyle.State_Enabled | QtWidgets.QStyle.State_Horizontal | QtWidgets.QStyle.State_Active
		# Draw first handle
		self.initStyleOption(self.opt)
		self.opt.subControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
		self.opt.sliderPosition = self.first_position
		self.opt.state = def_state
		self.opt.state |= QtWidgets.QStyle.State_MouseOver
		# self.opt.state |= QtWidgets.QStyle.State_Sunken if self.press_state == 0 else def_state
		self.opt.rect =	style.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, 
											self.opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, painter, self)
		
		# Draw second handle
		self.initStyleOption(self.opt)
		self.opt.subControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
		self.opt.sliderPosition = self.second_position
		self.opt.state = def_state
		self.opt.state |= QtWidgets.QStyle.State_MouseOver
		# self.opt.state |= QtWidgets.QStyle.State_Sunken if self.press_state == 1 else def_state
		self.opt.rect =	style.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, 
											self.opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, self.opt, painter, self)
		self.initStyleOption(self.opt)

	def mousePressEvent(self, event):
		self.opt.sliderPosition = self.first_position
		self._first_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, self.opt, event.pos(), self
		)

		self.opt.sliderPosition = self.second_position
		self._second_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, self.opt, event.pos(), self
		)

		if self._first_sc == QtWidgets.QStyle.SC_SliderHandle:
			self.press_state = 0
		elif self._second_sc == QtWidgets.QStyle.SC_SliderHandle:
			self.press_state = 1
		else:
			self.press_state = -1
		self.update()

	def mouseReleaseEvent(self, event) -> None:
		self.press_state = -1
		self.update()

	def mouseMoveEvent(self, event):
		if self.press_state == -1:
			self.opt.sliderPosition = self.first_position
			first_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, self.opt, event.pos(), self )

			self.opt.sliderPosition = self.second_position
			second_sc = self.style().hitTestComplexControl(
				QtWidgets.QStyle.CC_Slider, self.opt, event.pos(), self )
			
			if first_sc == QtWidgets.QStyle.SC_SliderHandle:
				self.hover_state = 0
			elif second_sc == QtWidgets.QStyle.SC_SliderHandle:
				self.hover_state = 1
			else:
				self.hover_state = -1
			self.update()
			return

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
		# self.valueChanged.emit(self.first_position, self.second_position)

	def sizeHint(self):
		SliderLength = 84
		TickSpace = 5

		w = SliderLength
		h = self.style().pixelMetric(QtWidgets.QStyle.PM_SliderControlThickness, self.opt, self)
		if (
			self.opt.tickPosition.value & QtWidgets.QSlider.TickPosition.TicksAbove.value
			or self.opt.tickPosition.value & QtWidgets.QSlider.TickPosition.TicksBelow.value
		):
			h += TickSpace

		return self.style().sizeFromContents(QtWidgets.QStyle.CT_Slider, self.opt, QtCore.QSize(w, h), self)
		