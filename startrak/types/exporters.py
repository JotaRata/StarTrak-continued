
from io import TextIOWrapper
from startrak.native.abstract import STExporter
from startrak.native.ext import STObject


class TextExporter(STExporter):
	def __init__(self, path : str) -> None:
		# Simple text exporter, no need to check for extension
		self.path = path
	
	def __enter__(self):
		self._file = open(self.path, 'w')
		return self._file
	
	def __exit__(self) -> None:
		self._file.__exit__()

	def write(self, obj: STObject):
		indentation = '  '
		separator = ': '

		self._file.write(type(obj).__name__ + separator )
		for key, value in obj.__export__():
			if isinstance(value, STObject):
				self._file.write(indentation + key + separator + value.__pprint__(2))
			else:
				self._file.write(indentation + key + separator  + repr(value))