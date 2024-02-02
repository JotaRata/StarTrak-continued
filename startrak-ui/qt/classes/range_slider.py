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

		self.setMaximum(1000)

		self.press_state = -1
		self.hover_state = -1
		self.mouseReleaseEvent(None)

		self.hoverRect = QtCore.QRect()
		self.setOrientation(QtCore.Qt.Orientation.Horizontal)
		self.setFocusPolicy(QtGui.Qt.FocusPolicy(self.style().styleHint(QtWidgets.QStyle.StyleHint.SH_Button_FocusPolicy)))

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

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		style = self.style()
		opt = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(opt)
		opt.subControls = QtWidgets.QStyle.SubControl.SC_SliderGroove | QtWidgets.QStyle.SubControl.SC_SliderTickmarks

		#   Draw GROOVE
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, opt, painter, self)
		self.initStyleOption(opt)
		#  Draw INTERVAL
		color = self.palette().color(QtGui.QPalette.Highlight)
		color.setAlpha(160)
		painter.setBrush(QtGui.QBrush(color))
		painter.setPen(QtCore.Qt.NoPen)
		opt.sliderPosition = self.first_position
		x_left_handle = (
			style
			.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
			.right() )
		opt.sliderPosition = self.second_position
		x_right_handle = (
			style
			.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
			.left() )
		groove_rect = style.subControlRect(
			QtWidgets.QStyle.ComplexControl.CC_Slider, opt, QtWidgets.QStyle.SubControl.SC_SliderGroove, self
		)
		selection = QtCore.QRect(
			x_left_handle,
			groove_rect.y(),
			x_right_handle - x_left_handle,
			groove_rect.height(), ).adjusted(-1, 1, 1, -1)
		painter.drawRect(selection)

		# Draw first handle
		self.initStyleOption(opt, 0)
		opt.state |= QtWidgets.QStyle.State_MouseOver if self.hover_state == 0 else QtWidgets.QStyle.State_None
		opt.rect =	style.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, 
											opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, opt, painter, self)
		
		# Draw second handle
		self.initStyleOption(opt, 1)
		opt.state |= QtWidgets.QStyle.State_MouseOver if self.hover_state == 1 else QtWidgets.QStyle.State_None
		opt.rect =	style.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider, 
											opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self)
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, opt, painter, self)

	def mousePressEvent(self, event):
		opt = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(opt, 0)
		self._first_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, opt, event.pos(), self
		)

		self.initStyleOption(opt, 1)
		self._second_sc = self.style().hitTestComplexControl(
			QtWidgets.QStyle.CC_Slider, opt, event.pos(), self
		)

		if self._first_sc == QtWidgets.QStyle.SC_SliderHandle:
			self.press_state = 0
		elif self._second_sc == QtWidgets.QStyle.SC_SliderHandle:
			self.press_state = 1
		else:
			self.press_state = -1
		self.disp_start = event.pos()

	def mouseReleaseEvent(self, event) -> None:
		self.press_state = -1
		self.hover_state = -1
		self._first_sc = QtWidgets.QStyle.SubControl.SC_None
		self._second_sc = QtWidgets.QStyle.SubControl.SC_None

	def mouseMoveEvent(self, event):
		if event.type() != QtCore.QEvent.Type.MouseMove:
			return
		if self.press_state == -1:
			self.initStyleOption(self.opt, 0)
			first_sc = self.style().hitTestComplexControl(
				QtWidgets.QStyle.CC_Slider, self.opt, event.pos(), self
			)

			self.initStyleOption(self.opt, 1)
			second_sc = self.style().hitTestComplexControl(
				QtWidgets.QStyle.CC_Slider, self.opt, event.pos(), self
			)

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
			0, distance, event.pos().x(), self.rect().width() )

		if self._first_sc == QtWidgets.QStyle.SC_SliderHandle:
			if pos <= self.second_position:
					self.first_position = pos
		elif self._second_sc == QtWidgets.QStyle.SC_SliderHandle:
			if pos >= self.first_position:
					self.second_position = pos
		self.update()

	def initStyleOption(self, option, handle= -1):
		super().initStyleOption(option)
		if handle == -1:
			if self.hover_state == 0:
				option.subControls = QtWidgets.QStyle.SC_SliderHandle
				option.sliderPosition = self.first_position
				option.sliderValue = self.first_position
			elif self.hover_state == 1:
				option.subControls = QtWidgets.QStyle.SC_SliderHandle
				option.sliderPosition = self.second_position
				option.sliderValue = self.second_position
			else:
				option.subControls = QtWidgets.QStyle.SC_None
			return
		option.subControls = QtWidgets.QStyle.SC_SliderHandle
		option.sliderPosition = self.first_position if handle == 0 else self.second_position
		option.sliderValue = self.first_position if handle == 0 else self.second_position

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
		