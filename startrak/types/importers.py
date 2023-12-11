
from ast import literal_eval
from importlib.resources import read_text
from typing import IO, Any, List, Tuple
from startrak.native.abstract import STImporter
from startrak.native.ext import AttrDict, STObject


class TextImporter(STImporter)
	_indent : str
	_sep : str

	def __init__(self, path : str, indentation = '  ', separator = ':') -> None:
		self.path = path
		self._indent = indentation
		self._sep = separator
	
	def __enter__(self) -> IO:
		self._file = open(self.path, 'r')
		return self._file
	
	def __exit__(self) -> None:
		return self._file.__exit__()

	def get_indent(self, line : str) -> int:
		return line.rstrip().count(self._indent)

	def parse_block(self, lines : List[str], index : int, current_indent : int) -> Tuple[AttrDict, int]:
		obj = AttrDict()

		while index < len(lines):
			line = lines[index].strip()
			if line:
				if line.startswith(('#', '!', '//', '%')):
					continue
				indent = self.get_indent(line)
				if indent == current_indent:
					if not obj: 
						obj['_type'] = line.rstrip(':')
					else:
						key, value = line.split(':', 1)
						obj[key.strip()] = literal_eval(value.strip())
				elif indent > current_indent:
					key, value = line.split(':', 1)
					sub_obj, index = self.parse_block(lines, index + 1, indent)
					obj[key.strip()] = sub_obj
				else:
					return obj, index
			index += 1
		return obj, index
	
	def read(self) -> STObject:
		lines = self._file.readlines()
		parsed_data, _ = self.parse_block(lines, 0, 0)
		
		def process_(attributes : AttrDict):
			main_type =attributes.pop('_type')
			for attr, value in attributes.items():
				if type(value) is dict:
					sub_dict = attributes[attr]
					attributes[attr] = process_(sub_dict)
			return STObject.__import__(attributes)
		return process_(parsed_data)