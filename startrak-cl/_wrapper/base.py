from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, NamedTuple

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

@dataclass
class _CommandInfo:
	name : str
	args : list[Positional | Optional]
	_kws : list[Keyword]
	ref : Callable

	def __post_init__(self):
		self.keywords = {k.key: k.types for k in self._kws} if self._kws else {}

	def __call__(self, args : list[str]):
		self.ref(self, args)

_REGISTERED_COMMANDS = dict[str, _CommandInfo]()

def register(name : str, *, args : list[Positional] = None, kw : list[Keyword] = None):
	def decorator(func):
		command = _CommandInfo(name, args, kw, func)
		_REGISTERED_COMMANDS[name] = command
		return command
	return decorator

def get_command(name) -> _CommandInfo | None:
	return _REGISTERED_COMMANDS.get(name, None)