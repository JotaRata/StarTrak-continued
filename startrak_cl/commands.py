from __future__ import annotations
import inspect
import os
import sys
from typing import Any, Callable, Self
from packaging.version import Version


class CommandBuilder:
	def __init__(self, name : str, version : str = "1.0.0"):
		self._name = name
		self._version = version
		self._imports = list[str]()
		self._params = list[Parameter]()

		self._file_name : str = None
		self._block_start = None
		self._block_end = None

	def add_author(self, author : str) -> Self:
		assert type(author) is str
		self._author = author
		return self
	
	def add_description(self, description : str) -> Self:
		assert type(description) is str
		self._desc = description
		return self

	def add_manual(self, manual_file : str) -> Self:
		assert type(manual_file) is str
		assert os.path.isfile(manual_file)
		self._man = manual_file
		return self
	
	def add_import(self, package_name : str) -> Self:
		assert type(package_name) is str
		self._imports.append(package_name)
		return self
	
	def add_parameter(self, parameter : Parameter) -> Self:
		assert isinstance(parameter, Parameter)
		self._params.append(parameter)
		return self
	
	def __enter__(self):
		return self
	
	def __exit__(self, *args):
		pass

	def get_context(self) -> CommandExecutor:
		return CommandExecutor(self)
	
	# def executes(self, function : Callable[..., Output]) -> Self:
	# 	assert callable(function)
	# 	self._function = function
	# 	return self


class Parameter:
	def __init__(self, name : str):
		self._name = name
	
	def with_type(self, parameter_type : type) -> Self:
		assert type(parameter_type) is type
		self._type = parameter_type
		return self
	
	def with_validation(self, validator : Callable[[object], bool]) -> Self:
		assert callable(validator)
		self._validator = validator
		return self
	
	def with_description(self, description : str) -> Self:
		assert isinstance(description, str)
		self._desc = description
		return self
	

class Optional(Parameter):
	def __init__(self, name : str, short_name : str = None):
		super().__init__(name)
		self._short = short_name
		self._type = bool

	def with_default(self, default : object) -> Self:
		self._default = default
		return self
	

class Output:
	def returns_value(self, value : object) -> Self:
		self._value = value
		return self
	
	def returns_text(self, source : Callable[..., str], **kwargs) -> Self:
		assert callable(source)
		self._text_source = source, kwargs
		return self
	
class CommandExecutor:
	def __init__(self, builder : CommandBuilder):
		self._builder = builder
		
	def __enter__(self):
		sys.settrace(lambda *args, **keys: None)
		frame = sys._getframe(1)
		frame.f_trace = self.trace

		return CommandExecutor.CommandHelper()
	
	def trace(self, frame, event, arg):
		raise CommandExecutor.SkipBlockExecution('Make sure to encapsulate the code in try/except')

	def __exit__(self, type, value, traceback):
		frame = inspect.currentframe()
		try:
			info = inspect.getframeinfo(frame.f_back)
			self._builder._file_name = info.filename
			self._builder._block_start = info.positions.lineno
			self._builder._block_end = info.positions.end_lineno
		finally:
			del frame
		if type is CommandExecutor.SkipBlockExecution:
			return True
		return False

	class CommandHelper:
		def print(self, value : str):
			print(value)
		def read(self):
			pass
	
	class SkipBlockExecution(Exception):
		pass

def register_command(command : CommandBuilder) -> CommandBuilder:
	return command