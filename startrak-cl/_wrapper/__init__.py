from typing import Callable
from .base import _REGISTERED_COMMANDS, _CommandInfo, Keyword, Positional, Optional, OptionalKeyword, TextRetriever
from .base import ReturnInfo

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
def path(__r : ReturnInfo | str):
	''' path in an object or string or name if it's not available'''
	if type(__r) is str:
		return __r
	if __r.path:
		return str(__r.path)
	return str(__r.name)
def obj(__r : ReturnInfo):
	''' Strictly the object of ReturnInfo '''
	return str(__r.obj)

def pos(index : int, kind : type):
	return Positional(index, kind)
def opos(index : int, kind : type):
	return Optional(index, kind)
def key(key : str, *kinds : type):
	return Keyword(key, *kinds)
def okey(key : str, kind : type, default = None):
	return OptionalKeyword(key, kind, default)

def get_text(source : Callable[..., str] | str, *args, **kwargs):
	return TextRetriever(source, *args, **kwargs)

def register(name : str, *, args : list[Positional] = None, kw : list[Keyword] = None):
	def decorator(func):
		command = _CommandInfo(name, args, kw, func if type(func) is not _CommandInfo else func.ref)
		_REGISTERED_COMMANDS[name] = command
		return command
	return decorator

def get_command(name) -> _CommandInfo | None:
	return _REGISTERED_COMMANDS.get(name, None)

def get_commands() -> list[str]:
	return list(_REGISTERED_COMMANDS.keys())
