
from typing import IO
from startrak.native.abstract import STExporter
from startrak.native.ext import STObject


class TextExporter(STExporter):
	_indent : str
	_sep : str

	def __init__(self, path : str, indentation = '  ', separator = ':') -> None:
		self.path = path
		self._indent = indentation
		self._sep = separator
	
	def __enter__(self) -> IO:
		self._file = open(self.path, 'w')
		return self._file
	
	def __exit__(self, *args) -> None:
		self._file.__exit__(*args)

	def write(self, obj: STObject):
		newline = '\n'

		self._file.write(type(obj).__name__ + self._sep )
		self._file.write(newline)
		for key, value in obj.__export__().items():
			if isinstance(value, STObject):
				self._file.write(self._indent + key + self._sep + value.__pprint__(2))
			else:
				self._file.write(self._indent + key + self._sep  + repr(value))
			self._file.write(newline)