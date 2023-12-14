
from ast import literal_eval
from typing import  Any, List, Self, Tuple
from startrak.native.abstract import STImporter
from startrak.native.ext import AttrDict, STObject, get_stobject


class TextImporter(STImporter):
	_indent : str
	_sep : str

	def __init__(self, path : str, indentation = '  ', separator = ': ') -> None:
		self.path = path
		self._indent = indentation
		self._sep = separator
	
	def __enter__(self) -> Self:
		self._file = open(self.path, 'r')
		return self
	
	def __exit__(self, *args) -> None:
		return self._file.__exit__(*args)

	def get_indent(self, line : str) -> int:
		return line.rstrip().count(self._indent)

	def parse_block(self, lines : List[str], index : int, current_indent : int) -> Tuple[AttrDict, int]:
		obj = dict[str, Any]()
		def_pending = None
		# print('\nparse_block at line', index)
		while index < len(lines):
			line = lines[index].rstrip()
			if line and not line.startswith(('#', '!', '//', '%')):
				# print(line)
				indent = self.get_indent(line)
				if indent == current_indent:
					if not obj: 
						current_indent += 1
						obj['_type'] = line.lstrip().rstrip(':')
						# print("setting obj type", line.rstrip(':'), current_indent-1)
					else:
						key, value = line.split(':', 1)
						if not value or value.isspace():
							def_pending = key
							# print('expecting object at line', line)
						else:
							# print('parsing', key, value)
							try:
								obj[key.strip()] = literal_eval(value.strip())
							except:
								raise AttributeError("Unable to parse", value) from None
				elif indent > current_indent and def_pending:
						key, value = line.split(':', 1)
						# print('recursive call on', key, value, )
						sub_obj, new_index = self.parse_block(lines, index, indent)
						obj[def_pending.strip()] = sub_obj
						def_pending = None
						index = new_index - 1
					# current_indent -= 1
				else:
					if def_pending:
						raise ValueError(f'Invalid syntax; expecting an object after line {index}: "{line}"')
					else:
						# print('Early return at line', index, line)
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
			
			cls = get_stobject(main_type)
			return cls.__import__(attributes)
			
		return process_(parsed_data)