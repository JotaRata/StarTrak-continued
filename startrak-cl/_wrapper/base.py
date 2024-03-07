from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

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
		return self.ref(self, args)

_REGISTERED_COMMANDS = dict[str, _CommandInfo]()

def register(name : str, *, args : list[Positional] = None, kw : list[Keyword] = None):
	def decorator(func):
		command = _CommandInfo(name, args, kw, func if type(func) is not _CommandInfo else func.ref)
		_REGISTERED_COMMANDS[name] = command
		return command
	return decorator

def get_command(name) -> _CommandInfo | None:
	return _REGISTERED_COMMANDS.get(name, None)