from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Callable, Generic, Type, TypeVar
from io import StringIO
from types import CodeType

from numpy import mat
from numpy.core.defchararray import rstrip
import startrak
import base
from processing.protocols import STException
__all__ = ['load_definition']

SYMBOL_PATTERN = re.compile(r'\$([\w-]+\b|\d+\b)')
FUNCTION_PARAMS = re.compile(r'(.+)\s*\((.*?)\)')

@dataclass(frozen= True)
class Command:
	name : str
	file : str
	arguments : list[Argument]
	doc_offsets : tuple[int, int]
	code : CodeType
	
	def execute(self, *params : str):

		args = {('ARG_' + str(arg.key)) if type(arg.key) is int else 
					(arg.key.removeprefix('-').replace('-','_').upper()) : arg.get_value(params)
					for arg in self.arguments}
		exec(self.code, EXEC_GLOBALS, args)
		return args.get('RETVAL', None)
	
	@property
	def docstring(self):
		with open(self.file, 'r') as f:
			f.seek(self.doc_offsets[0])
			text = f.read(self.doc_offsets[1] - self.doc_offsets[0])
		return text
	
	def __repr__(self) -> str:
		return f'{self.name} {" ".join(arg.key for arg in self.arguments)}'

T = TypeVar('T')
class Argument(Generic[T]):
	key : int | str
	caster : Callable[..., T] | Type[T]
	default : T = None

	def __init__(self, key : str,  caster : Callable[..., T] | Type[T], default: T = None):
		self.key = int(key) if key.isdigit() else key
		self.caster = caster
		self.default = default

	def get_value(self, arg_list : list[str]) -> T:
		positional = type(self.key) is int
		index : int

		if positional:
			index = self.key
		else:
			if not self.key in arg_list:
				return False if self.caster is bool else None
			elif self.caster is bool:
				return True
			index = arg_list.index(self.key) + 1

		if index >= len(arg_list):
			if self.default == None:
				raise STException(f'Expected argument at position #{index + 1}')
			raw_value = self.default
		else:
			raw_value = arg_list[index]
		
		try:
			value = self.caster(raw_value)
		except:
			raise STException(f'Invalid argument type at position #{index + 1}')
		return value
	
	def __repr__(self) -> str:
		return f'({self.key} : {self.caster.__name__} : {self.default})'

class _Types:
	@staticmethod
	def text(ret : _ReturnValue | str):
		if type(ret) is str:
			return ret
		if ret.text:
			return ret.text.get_str()
		if ret.value:
			return str(ret.value)
		return None
	@staticmethod
	def path(ret : _ReturnValue | str):
		if type(ret) is str:
			return ret.replace(r'\\', '/')
		if ret.path:
			return str(ret.path).replace(r'\\', '/')
		return None
	@staticmethod
	def name(ret : _ReturnValue | str):
		if type(ret) is str:
			return ret
		if ret.value:
			if isinstance(ret.value, startrak.native.classes.STObject):
				return ret.value.name
			return type(ret.value).__name__
		return None
	@staticmethod
	def int(ret : _ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if value:
			return int(value)
		return None
	@staticmethod
	def float(ret : _ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if value:
			return float(value)
		return None
	@staticmethod
	def str(ret : _ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if value:
			return str(value)
		return None
	@staticmethod
	def bool(ret : _ReturnValue | bool):
		value = ret if type(ret) is bool else ret.value
		if value:
			return bool(value)
		return False
	@staticmethod
	def vector(ret : _ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if type(value) is tuple:
			return value
		elif type(value) is str:
			match = re.match(r'(\d+)', value)
			if match:
				return tuple(float(group) for group in match.groups())
		return None

arg_type = { key : getattr(_Types, key) for key in dir(_Types) if not key.startswith('_')}

def load_definition(path : str, allow_imports : bool = True) -> Command:
	# First pass: Read and parse file by sections
	with open(path, 'r') as f:
		status = -1
		header = ''
		
		current_byte = 0
		doc_start = 0
		doc_end = 0
		body = StringIO()
		return_output = dict[str, object]()
		
		for line in iter(f.readline, ''):
			if not line or line.startswith('#'):
				continue
			if 'import' in line and not allow_imports:
				continue
			
			mod = False
			if status == -1:
				header = line
				status = 0
			else:
				if '<!BODY>' in line:
					status = 1
					continue
				if '<!DOC>' in line:
					status = 2
					doc_start = f.tell()
					continue
				if '<!END>' in line:
					if status == 2:
						doc_end = current_byte
					status = 0
					continue
			current_byte = f.tell()
			
			match status:
				case 0 | 2:		# parsing nothing or docs
					continue
				case 1:			# Parsing Body
					if '$' in line:
						match = SYMBOL_PATTERN.findall(line)
						if not match:
							continue
						for group in match:
							if group.isnumeric():
								line = line.replace('$'+ group, 'ARG_' + group)
							else:
								line = line.replace('$'+ group, group.removeprefix('-').replace('-', '_').upper())

					if line.lstrip().startswith('ERROR'):
						_, msg = line.split(maxsplit= 1)
						body.write(line.replace('ERROR', 'raise STException(').rstrip() + ')\n')
						continue

					if line.startswith('RETURN'):
						_, token, *trail = line.split()
						value = ' '.join(trail)

						match token:
							case 'VALUE':
								return_output['value'] = value
							case 'TEXT':
								match = FUNCTION_PARAMS.match(value)
								if not match:
									raise SyntaxError('Invalid syntax in text method parameters')
								name, args = match.groups()
								return_output['text'] = f'_TextMethod({name}, {args})'
							case 'PATH':
								return_output['path'] = value
							case _:
								raise SyntaxError(f'Unknown token "{token}"')
						continue

					body.write(line)

				case _:
					raise IOError('Invalid syntax in command definition.')

	# Second pass: Extract definition from header
	name, *tokens = header.strip().split(' ')
	args = list[Argument]()

	for token in tokens:
		assert ':' in token, 'Invalid syntax in command header'
		key, kind, *extras = token.split(':')

		assert len(key) > 1, f'Missing index for token: {key}'
		args.append(Argument(key[1:], arg_type[kind], extras[0] if extras else None))
		

	# Third pass: Format body tags
	if return_output:
		body.write(f'RETVAL = _ReturnValue(')
		for key in return_output:
			body.write(f'{key}= {return_output[key]}, ')
		body.write(f')')
	body.seek(0)
	# print(body.getvalue())
	code = compile(body.getvalue(), filename= name, mode= 'exec')
	return Command(name, file = path, arguments = args, doc_offsets = (doc_start, doc_end), code= code)

@dataclass(frozen= True, slots= True)
class _ReturnValue:
	value : object = None
	text : _TextMethod = None
	path : str = None

class _TextMethod:
	def __init__(self, source : Callable[..., str], *args, **kwargs) -> None:
		self.source = source
		self.args = args
		self.kwargs = kwargs
	def __str__(self) -> str:
		if type(self.source) is str:
			return self.source
		return self.source(*self.args, **self.kwargs)
	def get_str(self) -> str:
		return self.__str__()
	

EXEC_GLOBALS =  {var : vars(startrak)[var] for var in dir(startrak)} |\
					{var : vars(base)[var] for var in dir(base)}
					# {'STException' : STException, 'ReturnValue' : _ReturnValue, 'TextMethod' : _TextMethod}