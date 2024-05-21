from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.policy import default
import os
import re
import sys
from typing import Callable, Generic, NamedTuple, Type, TypeVar
sys.path.append(os.getcwd() + '/startrak-cl')

from io import StringIO
from types import CodeType
import startrak
import base
from base.interface import INTERACTIVE_ADD, INTERACTIVE_EDIT, INTERACTIVE_LIST, INTERACTIVE_SERVER
from processing.protocols import STException


EXEC_GLOBALS =  {'startrak.' + var : vars(startrak)[var] for var in dir(startrak)} |\
					{'os.' + var : vars(os)[var] for var in ['getcwd']} |\
					{var : vars(base)[var] for var in dir(base)} | {'STException' : STException}

SYMBOL_PATTERN = re.compile(r'\$([\w-]*\b|\d*\b)')

@dataclass(frozen= True)
class Command:
	name : str
	arguments : list[Argument]
	docstring : StringIO
	code : CodeType
	
	def __call__(self, helper : base.Helper):
		args = {'ARG_' + i : helper.get_arg(i) for i in range(len(self.arguments))}
		kws = {arg.key.replace('-','_').upper() : helper.get_kw(arg.key) for arg in self.keywords}
		
		locals = args | kws
		exec(self.code, EXEC_GLOBALS, locals)
		return locals.get('RETVAL', None)
	
	def __repr__(self) -> str:
		return f'{self.name} {" ".join(arg.kind for arg in self.arguments)}  {" ".join(arg.key for arg in self.keywords)}'

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
				return self.default
			index = arg_list.index(self.key) + 1

		if index > len(arg_list):
			if self.default != None and positional:
				return self.default
			raise STException(f'Expected argument at position #{index + 1}')
		try:
			value = self.caster(arg_list[index])
		except:
			raise STException(f'Invalid argument type at position #{index + 1}')
		return value

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
		body = StringIO()
		doc = StringIO()
		
		for line in f:
			if not line or line.startswith('#'):
				continue
			if 'import' in line:
				continue

			if status == -1:
				header = line
				status = 0
			else:
				if '<!BODY>' in line:
					status = 1
					continue
				if '<!DOC>' in line:
					status = 2
					continue
				if '<!END>' in line:
					status = 0
					continue
			
			if status == 1:
				if line.startswith('return'):
					line = line.replace('return', 'RETVAL = ')
				body.write(line)
			elif status == 2: 
				doc.write(line)
			elif status == 0:
				continue
			else:
				raise IOError('Invalid syntax in command definition.')
	body.seek(0)

	# Second pass: Extract definition from header
	name, *tokens = header.strip().split(' ')
	args = list[Argument]()

	for token in tokens:
		assert ':' in token, 'Invalid syntax in command header'
		key, kind, *extras = token.split(':')

		if key.startswith('&'):
			assert len(key) > 1, f'Missing index for token: {key}'
			args.append(Argument(key[1:], arg_type[kind] ))
		

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
					newline = newline.replace('$'+ group, group.replace('-', '_').upper())

			body.seek(offset)
			body.write(newline)
		offset = body.tell()

	code = compile(body.getvalue(), filename= name, mode= 'exec')
	return Command(name, arguments=args, keywords= kws, docstring= doc, code= code)

cmd = load_definition(r"C:\Users\jjbar\Documents\GitHub\StarTrak-continued\startrak-cl\base\commands\session.stc")