from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, NamedTuple
from _process.protocols import STException

def name(__r : ReturnInfo | str):
	''' Name of an object or string'''
	if type(__r) is str:
		return __r
	return str(__r.name)
def text(__r : ReturnInfo | str):
	''' Text in an object or string'''
	if type(__r) is str:
		return __r
	return str(__r.text)
def obj(__r : ReturnInfo):
	''' Strictly the object of ReturnInfo '''
	return str(__r.obj)

class Positional:
	def __init__(self, index : int, kind : type) -> None:
		self.index = index
		self.type = kind
class Optional(Positional):
	pass
class Keyword:
	def __init__(self, key : str, *kinds : type) -> None:
		self.key = key
		self.types = kinds
		if not self.types:
			self.types = tuple()
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
	_kws : list[Keyword]
	ref : Callable

	def __post_init__(self):
		if not self.args:
			self.args = []
		if not self._kws:
			self._kws = []
		self.printable = True
		self.keywords = {k.key: k.types for k in self._kws}
		self.count_positional = sum(1 for arg in self.args if type(arg) is Positional)
		self.count_optional = sum(1 for arg in self.args if type(arg) is Optional)
		self.count_kws = sum(1 + len(arg.types) for arg in self._kws)

	def __call__(self, args : list[str]):
		helper = Helper(self, args)
		retval = self.ref(helper)
		if retval and type(retval) is not ReturnInfo:
			raise STException(f'Invalid reeturn type for "{self.name}"')
		return retval


class Helper:
	def __init__(self, command : _CommandInfo, args : list[str]) -> None:
		self.args = args
		self.command = command
	
	def get_kw(self, arg : str):
		types = self.command.keywords[arg]
		if len(self.args) < 1 + len(types): 
			return False
		if arg not in self.args: 
			return False
		idx = self.args.index(arg)
		if len(types) == 0:
			return True
		values = []
		for j, _type in enumerate(types, 1):
			next_ = self.args[idx + j]
			try:
				value = _type(next_)
			except:
				raise STException(f'Invalid argument type for "{self.command.name}" at position #{j}')
			values.append(value)
		if len(values) > 1:
			return values
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
def register(name : str, *, args : list[Positional] = None, kw : list[Keyword] = None):
	def decorator(func):
		command = _CommandInfo(name, args, kw, func if type(func) is not _CommandInfo else func.ref)
		_REGISTERED_COMMANDS[name] = command
		return command
	return decorator

def get_command(name) -> _CommandInfo | None:
	return _REGISTERED_COMMANDS.get(name, None)