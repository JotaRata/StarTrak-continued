from __future__ import annotations
import glob
import os
from base.helper import _ReturnValue
import startrak
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
