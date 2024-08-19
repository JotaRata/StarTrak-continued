from __future__ import annotations
from dataclasses import dataclass
import glob
import os
import re
import sys
from typing import Callable, Generic, Type, TypeVar, TYPE_CHECKING
from io import IOBase, StringIO
from types import CodeType

import _globals
import startrak
from processing.protocols import STException

if TYPE_CHECKING:
	from console.consoleapp import ConsoleApp
__all__ = ['load_definition']

SYMBOL_PATTERN = re.compile(r'\$([\w-]+\b|\d+\b)')
FUNCTION_PARAMS = re.compile(r'(.+)\s*\((.*?)\)')
SPLIT_LIST = re.compile(r',|\s')

@dataclass(frozen= True)
class Command:
	name : str
	file : str
	arguments : list[Argument]
	doc_offsets : tuple[int, int]
	code : CodeType
	persistent : dict[str, object] = None
	imports : list[str] = None
	
	# todo: move parsing logic to dedicated module
	def execute(self, params : list[str], printable : bool = True):
		parsed_args = self.parse_arguments(params)
		variables = {arg.name : value for arg, value in parsed_args.items()} |\
						{	'console' : _ConsoleHelper(_globals.CONSOLE_INSTANCE),
							'PRINTABLE' : printable}
		if self.persistent:
			variables |= self.persistent
		body_locals = {}
		exec(self.code, EXEC_GLOBALS | variables, body_locals)
		return body_locals.get('RETVAL', None)
	
	def parse_arguments(self, params : list[str]):
		positional = [arg for arg in self.arguments if arg.positional]
		keywords = [arg for arg in self.arguments if not arg.positional]

		output = dict[Argument, object]()
		for argument in keywords:
			if argument.key in params:
				if argument.caster is arg_type['bool']:
					output[argument] = True
					params.remove(argument.key)
					continue
				index = params.index(argument.key)
				output[argument] = argument.get_value(params[index + 1])
				params.pop(index + 1)
				params.pop(index)
			elif argument.default is not None:
				output[argument] = argument.default
			elif argument.caster is arg_type['bool']:
				output[argument] = False

		for argument in positional:
			if argument.key < len(params):
				output[argument] = argument.get_value(params[argument.key])
			elif argument.default is not None:
				output[argument] = argument.default
			else:
				raise STException(f'Expected argument at position #{argument.key + 1}')
		return output

	def get_documentation(self):
		with open(self.file, 'r') as f:
			f.seek(self.doc_offsets[0])
			text = f.read(self.doc_offsets[1] - self.doc_offsets[0])
		return text
	
	def read_documentation(self):
		f = open(self.file, 'r')
		f.seek(self.doc_offsets[0])

		def iterator(file):
			offset = self.doc_offsets[0]
			for line in file:
				if offset >= self.doc_offsets[1]:
					break
				offset += len(line)
				yield line
			file.close()
		return iterator(f)
	
	def __repr__(self) -> str:
		return f'{self.name} {" ".join(str(arg.key) for arg in self.arguments)}'

T = TypeVar('T')
class Argument(Generic[T]):
	key : int | str
	caster : Callable[..., T] | Type[T]
	default : T = None

	def __init__(self, key : str,  caster : Callable[..., T] | Type[T], default: T = None):
		self.key = int(key) if key.isdigit() else '-' + key
		self.positional = type(self.key) is int
		self.caster = caster
		self.default = caster(default) if default else None
	
	@property
	def name(self) -> str:
		if self.positional:
			return 'ARG_' + str(self.key)
		return self.key.removeprefix('--').removeprefix('-').replace('-','_').upper()
		
	def get_value(self, raw_value : str) -> T:
		try:
			value = self.caster(raw_value)
		except Exception as e:
			raise STException(f'Invalid argument type: {raw_value}', e)
		return value
	
	def __str__(self) -> str:
		return f'Argument ({self.key} : {self.caster.__name__} : {self.default})'


#! ----------------------- Helper classes -------------------------------
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
	def path(ret : _ReturnValue | str | list | tuple):
		value : list[str]
		if type(ret) is str:
			if '*' in ret:
				value = glob.glob(ret, root_dir= os.getcwd() + '/')
			else:
				value = [ret]
		elif isinstance(ret, (list, tuple)):
			value = [str(item) for item in ret]
		elif isinstance(ret, _ReturnValue):
			value = [str(item) for item in ret.path]
		else:
			return None
		if os.name == 'nt':
			value = [item.replace(r'\\', '/') for item in value]
		return value
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
			value = str(value)
			if value == '$null': # Return a falsely non-null string
				return ''
			return value
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

class _ConsoleHelper:
	def __init__(self, console : ConsoleApp) -> None:
		self._get_size = console.size
		self._get_name = lambda: getattr(type(console), '__name__', 'NULL')
		self.execute = console.process
		self.format = console.format
		self.clear = console.clear
		self.write = console.write
		self.flush = console.flush
	@property
	def width(self) -> int:
		return self._get_size()[1] - 1
	@property
	def height(self) -> int:
		return self._get_size()[0]
	@property
	def name(self) -> str:
		return self._get_name()
	
	def get_commands(self):
		return [cmd for cmd in get_commands()]
	
	def read_documentation(self, command_name):
		command = get_command(command_name)
		return command.read_documentation()
	def get_documentation(self, command_name):
		command = get_command(command_name)
		return command.get_documentation()
	def redirect(self, buffer : IOBase, close_buffer : bool = True):
		return _ConsoleOutputContext(buffer, close_buffer)
	def buffer(self, *args):
		return StringIO(*args)
	
class _ConsoleOutputContext:
	def __init__(self, buffer : IOBase, close_buffer : bool):
		self._buffer = buffer
		self._stdout = sys.stdout
		self._close = close_buffer
	def write(self, *args):
		return self._buffer.write(*args)
	def read(self, *args):
		return self._buffer.read(*args)
	def seek(self, *args):
		return self._buffer.seek(*args)
	def tell(self, ):
		return self._buffer.tell()
	def __enter__(self):
		sys.stdout = self._buffer
	def __exit__(self, *args):
		sys.stdout = self._stdout
		if self._close:
			self._buffer.close()

#! -------------------- Definition loading -------------------------------
def load_definition(path : str, allow_imports : bool = True) -> Command:
	# First pass: Read and parse file by sections
	with open(path, 'r') as f:
		status = -1
		header = ''
		
		current_byte = 0
		doc_start = 0
		doc_end = 0
		include_buffer = StringIO()
		body_buffer = StringIO()
		data_buffer = StringIO()
		data_names = list[str]()
		return_output = dict[str, object]()
		imports = list[str]()
		
		for line in iter(f.readline, ''):
			if not line or line.startswith('#'):
				continue

			if status == -1:
				header = line
				status = 0
			else:
				if status == 0:
					if '<!BODY>' in line:
						status = 1
						continue
					if '<!DOC>' in line:
						status = 2
						doc_start = f.tell()
						continue
					if '<!DATA>' in line:
						status = 3
						continue
					if '<!INCLUDE>' in line:
						status = 4
						continue
				if '<!END>' in line:
					if status == 2:
						doc_end = current_byte
					status = 0
					continue
			current_byte = f.tell()
			
			lstrip = line.lstrip()
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
								line = line.replace('$'+ group, group.removeprefix('--').removeprefix('-').replace('-', '_').upper())
					
					if lstrip.startswith(('import', 'from')):
						raise SyntaxError('Imports are not allowed inside <!BODY>. Use <!INCLUDE> instead')
					
					if lstrip.startswith('ERROR'):
						_, msg = line.split(maxsplit= 1)
						body_buffer.write(line.replace('ERROR', 'raise STException(').rstrip() + ')\n')
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
								command_name, args = match.groups()
								return_output['text'] = f'_TextMethod({command_name}, {args})'
							case 'PATH':
								return_output['path'] = value
							case _:
								raise SyntaxError(f'Unknown token "{token}"')
						continue
					body_buffer.write(line)
				case 3:			# Parsing data blocks
					if lstrip.startswith('SAVE'):
						_, var_name, *trail = line.split()
						if not var_name or trail:
							raise SyntaxError('Invalid syntax at data block.')
						data_names.append(var_name)
						continue
					data_buffer.write(line)
				case 4:			# Parsing includes
					if not allow_imports:
						continue
					if lstrip.startswith('import'):
						_, *module = SPLIT_LIST.split(lstrip)
						imports.extend(module)
						include_buffer.write(line)
					elif lstrip.startswith('from'):
						_, module, _, *inner = SPLIT_LIST.split(lstrip)
						imports.extend( inner)
						include_buffer.write(line)
				case _:
					raise IOError('Invalid syntax in command definition.')

	# Second pass: Extract definition from header
	command_name, *tokens = header.strip().split(' ')
	args = list[Argument]()

	for token in tokens:
		assert ':' in token, 'Invalid syntax in command header'
		key, kind, *extras = token.split(':')

		assert len(key) > 1, f'Missing index for token: {key}'
		args.append(Argument(key[1:], arg_type[kind], extras[0] if extras else None))
		

	# Third pass: Format body tags
	data_block = None
	if data_names:
		data_buffer.write('PERSISTENT = {')
		for var_name in data_names:
			data_buffer.write(f'"{var_name}" : {var_name}, ')
		data_buffer.write('}')
		data_buffer.seek(0)

		block_locals = {}
		block_compiled = compile(data_buffer.getvalue(), filename= command_name + '_persistent', mode= 'exec')
		exec(block_compiled, EXEC_GLOBALS, block_locals)
		data_block = block_locals.get('PERSISTENT', None)

	if return_output:
		body_buffer.write(f'RETVAL = _ReturnValue(')
		for key in return_output:
			body_buffer.write(f'{key}= {return_output[key]}, ')
		body_buffer.write(f')')
	
	if imports:
		imports = list(set(imports))
		include_buffer.write('globals().update({')
		include_buffer.write(', '.join( [f'"{i}" : {i}' for i in imports if i] ))
		include_buffer.write('})\n')

	include_buffer.seek(0)
	body_buffer.seek(0)

	main_buffer = StringIO()
	main_buffer.writelines(include_buffer.readlines())
	main_buffer.writelines(body_buffer.readlines())

	body_code = compile(main_buffer.getvalue(), 
							filename= command_name, mode= 'exec')

	return Command(command_name, file = path, arguments = args, 
						doc_offsets = (doc_start, doc_end), code= body_code,
						persistent= data_block, imports=  imports)

def get_command(name : str) -> Command:
	if name not in REGISTERED_COMMANDS:
		raise STException(f'Command not found: {name}')
	return REGISTERED_COMMANDS[name]

def get_commands():
	return REGISTERED_COMMANDS


#! ---------------------- Global scope -------------------------------------
EXEC_GLOBALS =  {method.__name__ : method for method in [
						STException, _ReturnValue, _TextMethod,
					]}
					# {'STException' : STException, 'ReturnValue' : _ReturnValue, 'TextMethod' : _TextMethod}

COMMAND_DIR = _globals.BASE_DIR + '/commands/'
REGISTERED_COMMANDS = dict[str, Command]()

for file in os.scandir(COMMAND_DIR):
	if not file.path.endswith('.stc'):
		continue
	
	command = load_definition(file.path, True)
	REGISTERED_COMMANDS[command.name] = command
	print('Command registered: ', file.path)
