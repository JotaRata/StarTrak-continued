from __future__ import annotations
from PySide6 import QtWidgets, QtCore
from typing import Sequence, cast


class Application(QtWidgets.QApplication):
	on_sessionLoad = QtCore.Signal(object, arguments= ['session'])
	
	def __init__(self, startrak_module, args : Sequence[str]):
		super().__init__(args)
		self.st_module = startrak_module

	@staticmethod
	def instance() -> Application:
		app = QtWidgets.QApplication.instance()
		assert app is not None
		return cast(Application, app)
		