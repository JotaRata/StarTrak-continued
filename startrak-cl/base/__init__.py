from typing import Callable
from .classes import _REGISTERED_COMMANDS, _CommandInfo, Keyword, Positional, Optional, OptionalKeyword, TextRetriever, ArgList
from .classes import ReturnInfo, Helper

# Parameter types
def name(__r : ReturnInfo | str):
	if type(__r) is str:
		return __r
	return str(__r.name)

def text(__r : ReturnInfo | str):
	if type(__r) is str:
		return __r
	return str(__r.text)

def path(__r : ReturnInfo | str):
	if type(__r) is str:
		return __r
	if __r.path:
		return str(__r.path)
	return str(__r.name)

def obj(__r : ReturnInfo):
	return str(__r.obj)


PositionalArg = Positional | Optional
KeywordArg = Keyword | OptionalKeyword

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
