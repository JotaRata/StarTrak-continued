
from typing import Any


_ST_METHODS = dict()
def get_method(name : str) -> tuple[Any | None, tuple[str, ...] | None, str | None]:
	methods = _ST_METHODS.get(name, None)
	if not methods:
		return None, None, None
	return methods[0]

def has_method(name : str):
	return name in _ST_METHODS

def ST_METHOD(name : str, *targs : str, ret : str = None):
	def decorator(func):
		if not name in _ST_METHODS:
			_ST_METHODS[name] = [(func, targs, ret)]
		else:
			_ST_METHODS[name].append([(func, targs, ret)])

		def wrapper(*args : tuple[str, str]):
			return func(*args)
		return wrapper
	return decorator

@ST_METHOD('session', ret= 'Session')
def _GET_SESSION():
	return 'get_session()'
@ST_METHOD('star', 'int|str', ret= 'Star')
def _GET_STAR(__index):
	return f'get_star({__index})'
@ST_METHOD('file', 'int|str', ret= 'FileInfo')
def _GET_FILE(__index):
	return f'get_file({__index})'
@ST_METHOD('open', 'str')
def _OPEN_SESSION(__path):
	return f'load_session({__path})'
@ST_METHOD('add', '&file','str')
def _ADD_FILE(__path):
	return f'load_file({__path})'
# @ST_METHOD('add', '&star','str')
# def _ADD_STAR(__path):
# 	return f'load_file({__path})'