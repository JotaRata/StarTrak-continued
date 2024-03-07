from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, NamedTuple
from _process.protocols import STException

class Positional:
	def __init__(self, index, kind) -> None:
		self.index = index
		self.type = kind
class Optional(Positional):
	pass
class Keyword:
	def __init__(self, key, *kinds) -> None:
		self.key = key
		self.types = kinds
		if not self.types:
			self.types = tuple()
class OptionalKeyword:
	def __init__(self, key, kind, default) -> None:
		self.key = key
		self.type = type
		self.default = default
class ReturnInfo(NamedTuple):
	name : str = None
	text : str = None
	obj : object = None
	def __str__(self) -> str:
		return self.name
	def __int__(self) -> str:
		return int(self.obj)


@dataclass
class _CommandInfo:
	name : str
	args : list[Positional | Optional]
	_kws : list[Keyword | OptionalKeyword]
	ref : Callable

	def __post_init__(self):
		if not self.args:
			self.args = []
		if not self._kws:
			self._kws = []
		self.printable = True
		self.keywords = {k.key: k for k in self._kws}
		self.count_positional = sum(1 for arg in self.args if type(arg) is Positional)
		self.count_optional = sum(1 for arg in self.args if type(arg) is Optional)
		self.count_kws = sum(1 + len(arg.types) for arg in self._kws)

	def __call__(self, args : list[str]):
		helper = Helper(self, args)
		retval = self.ref(helper)
		if retval and type(retval) is not ReturnInfo:
			raise STException(f'Invalid return type for "{self.name}"')
		return retval

class Helper:
	def __init__(self, command : _CommandInfo, args : list[str]) -> None:
		self.args = args
		self.command = command
	
	def get_kw(self, arg : str):
		if arg not in self.args: 
			return False
		key = self.command.keywords[arg]

		if type(key) is Keyword:
			if len(self.args) < 1 + len(key.types): 
				return False
			idx = self.args.index(arg)
			if len(key.types) == 0:
				return True
			values = []
			for j, _type in enumerate(key.types, 1):
				next_ = self.args[idx + j]
				try:
					value = _type(next_)
				except Exception as e:
					raise STException(f'Invalid argument type for "{self.command.name}" at position #{j}: {e}')
				values.append(value)
			if len(values) > 1:
				return values
			return value
		elif type(key) is OptionalKeyword:
			if len(self.args) < 1 + len(key.types): 
				return key.default
			idx = self.args.index(arg)
			_type = key.type
			try:
				value = _type(self.args[idx + 1])
			except:
				raise STException(f'Invalid argument type for "{self.command.name}" at position #1.')
			return value
			
	def get_arg(self, pos : int):
		_type = self.command.args[pos].type
		if pos > len(self.args):
			if type(self.command.args[pos]) is Optional:
					return None
			raise STException(f'Expected argument at position #{pos + 1} of the function "{self.command.name}"')
		try:
			value = _type(self.args[pos])
		except:
			print(pos, self.args, _type)
			raise STException(f'Invalid argument type for "{self.command.name}" at position #{pos + 1}')
		return value

	def print(self, *args, **kwargs):
		if self.command.printable:
			print(*args, **kwargs)

_REGISTERED_COMMANDS = dict[str, _CommandInfo]()