from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.policy import default
import os
import re
import sys
from typing import Callable, Generic, NamedTuple, Type, TypeVar
# sys.path.append(os.getcwd() + '/startrak-cl')

from io import StringIO
from types import CodeType
import startrak
import base
from base.interface import INTERACTIVE_ADD, INTERACTIVE_EDIT, INTERACTIVE_LIST, INTERACTIVE_SERVER
from processing.protocols import STException


EXEC_GLOBALS =  {var : vars(startrak)[var] for var in dir(startrak)} |\
					{var : vars(base)[var] for var in dir(base)} | {'STException' : STException}

SYMBOL_PATTERN = re.compile(r'\$([\w-]*\b|\d*\b)')

@dataclass(frozen= True)
class Command:
	name : str
	file : str
	arguments : list[Argument]
	doc_offsets : tuple[int, int]
	code : CodeType

	def docstring(self):
		with open(self.file, 'r') as f:
			f.seek(self.doc_offsets[0])
			text = f.read(self.doc_offsets[1] - self.doc_offsets[0])
		return text
	
	def __call__(self, *params : str):

		args = {('ARG_' + arg.key) if type(arg.key) is int else 
					(arg.key.removeprefix('-').replace('-','_').upper()) : arg.get_value(params)
					for arg in self.arguments}
		print(args)
		exec(self.code, EXEC_GLOBALS, args)
		return args.get('RETVAL', None)
	
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
				return None
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

@dataclass(frozen= True, slots= True)
class ReturnValue:
	value : object = None
	text : TextRetriever = None
	path : str = None

class TextRetriever:
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
	
class _Types:
	@staticmethod
	def text(ret : ReturnValue | str):
		if type(ret) is str:
			return ret
		if ret.text:
			return ret.text.get_str()
		if ret.value:
			return str(ret.value)
		return None
	@staticmethod
	def path(ret : ReturnValue | str):
		if type(ret) is str:
			return ret.replace(r'\\', '/')
		if ret.path:
			return str(ret.path).replace(r'\\', '/')
		return None
	@staticmethod
	def name(ret : ReturnValue | str):
		if type(ret) is str:
			return ret
		if ret.value:
			if isinstance(ret.value, startrak.native.classes.STObject):
				return ret.value.name
			return type(ret.value).__name__
		return None
	@staticmethod
	def int(ret : ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if value:
			return int(value)
		return None
	@staticmethod
	def float(ret : ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if value:
			return float(value)
		return None
	@staticmethod
	def str(ret : ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if value:
			return str(value)
		return None
	@staticmethod
	def vector(ret : ReturnValue | str):
		value = ret if type(ret) is str else ret.value
		if type(value) is tuple:
			return value
		elif type(value) is str:
			match = re.match(r'(\d+)', value)
			if match:
				return tuple(float(group) for group in match.groups())
		return None

arg_type = { key : getattr(_Types, key) for key in dir(_Types) if not key.startswith('_')}

def load_definition(path : str) -> Command:
	# First pass: Read and parse file by sections
	with open(path, 'r') as f:
		status = -1
		header = ''
		
		current_byte = 0
		doc_start = 0
		doc_end = 0
		body = StringIO()
		
		for line in iter(f.readline, ''):
			if not line or line.startswith('#'):
				continue
			#! Danger zone
			# if 'import' in line:
			# 	continue

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
				case 0 | 2:
					continue
				case 1:
					if line.startswith('return'):
						line = line.replace('return', 'RETVAL = ')
					body.write(line)
				case _:
					raise IOError('Invalid syntax in command definition.')
	body.seek(0)

	# Second pass: Extract definition from header
	name, *tokens = header.strip().split(' ')
	args = list[Argument]()

	for token in tokens:
		assert ':' in token, 'Invalid syntax in command header'
		key, kind, *extras = token.split(':')

		assert len(key) > 1, f'Missing index for token: {key}'
		args.append(Argument(key[1:], arg_type[kind], extras[0] if extras else None))
		

	# Third pass: Format body tags
	offset = body.tell()
	for line in body:
		if '$' in line:
			match = SYMBOL_PATTERN.search(line)
			if not match:
				continue
			newline = line

			for group in match.groups():
				if group.isnumeric():
					newline = newline.replace('$'+ group, 'ARG_' + group)
				else:
					newline = newline.replace('$'+ group, group.removeprefix('-').replace('-', '_').upper())

			body.seek(offset)
			if len(newline) < len(line):
				newline = newline.rstrip() + ' ' * (len(line) - len(newline)) + '\n'

			body.write(newline)
		offset = body.tell()

	code = compile(body.getvalue(), filename= name, mode= 'exec')
	return Command(name, file = path, arguments = args, doc_offsets = (doc_start, doc_end), code= code)
