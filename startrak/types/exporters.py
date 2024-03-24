
from io import BytesIO
from typing import Any, List, Self
from startrak.native.abstract import STExporter
from startrak.native.ext import STObject, is_stobj


class TextExporter(STExporter):
	_indent : str
	_sep : str

	def __init__(self, path : str, indentation = '  ', separator = ': ') -> None:
		self.path = path
		self._indent = indentation
		self._sep = separator
	
	def __enter__(self) -> Self:
		self._file = open(self.path, 'w')
		return self
	
	def __exit__(self, *args) -> None:
		self._file.__exit__(*args)

	def write_block(self, obj : Any, indent = 0) -> str:
		indentation = self._indent * indent
		obj_type = type(obj)

		lines : List[str] = ["", indentation + obj_type.__name__ + self._sep]
		for key, value in obj.__export__().items():
			if key in obj_type.__dict__ and  isinstance(obj_type.__dict__[key], property):
				continue
			if is_stobj(value) or hasattr(value, '__export__'):
				lines.append(indentation + self._indent + key + self._sep + self.write_block(value, indent + 2))
			else:
				value_str = str(value)
				if type(value) is str:
					value_str = f"'{value_str}'"
				lines.append(indentation + self._indent + key + self._sep  + value_str)
		return '\n'.join(lines)

	def write(self, obj: STObject):
		block = self.write_block(obj)
		self._file.write(block)


class BytesExporter(STExporter):
	def __init__(self) -> None:
		self._buffer = BytesIO()
	
	def __enter__(self) -> Self:
		return self
	def __exit__(self, *args) -> None:
		self._buffer.close()
	
	def data(self):
		if self._data:
			return self._data
	
	def convert(self, obj : Any) -> str:
		obj_type = type(obj)
		attrs = {'_type' : obj_type.__name__}

		for key, value in obj.__export__().items():
			if key in obj_type.__dict__ and  isinstance(obj_type.__dict__[key], property):
				continue
			if is_stobj(value) or hasattr(value, '__export__'):
				attrs[key] = self.convert(value)
			else:
				attrs[key] = value
		return attrs

	def write(self, obj: STObject):
		block = str(self.convert(obj))
		self._buffer.write(block.encode())
		self._data = self._buffer.getvalue()