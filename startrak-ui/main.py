# mypy: disable-error-code="attr-defined"
import sys, os
sys.path.insert(0, os.getcwd())

import startrak
from qt.extensions import *
from views import Application, MainView

if __name__ == "__main__":
	app = Application(startrak, [])
	app.setStyle('Fusion')

	main_view = MainView()
	main_view.show()
	app.exec()
else:
	raise ImportError('Cannot import module')