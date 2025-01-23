from __future__ import annotations
import os
from typing import Any, Callable, Self
from packaging.version import Version


class Command:
	def __init__(self, name : str, version : str = "1.0.0"):
		self.name = name
		self.version = version
		self.imports = list[str]()
		self.parameters = list[Parameter]()

	def add_author(self, author : str) -> Self:
		assert type(author) is str
		self.author = author
		return self
	
	def add_description(self, description : str) -> Self:
		assert type(description) is str
		self.description = description
		return self

	def add_manual(self, manual_file : str) -> Self:
		assert type(manual_file) is str
		assert os.path.isfile(manual_file)
		self.man_file = manual_file
		return self
	
	def add_import(self, package_name : str) -> Self:
		assert type(package_name) is str
		self.imports.append(package_name)
		return self
	
	def add_parameter(self, parameter : Parameter) -> Self:
		assert isinstance(parameter, Parameter)
		self.parameters.append(parameter)
		return self
	
	def executes(self, function : Callable[..., Output]) -> Self:
		assert isinstance(function, callable)
		self.function = function
		return self


class Parameter:
	def __init__(self, name : str):
		self.name = name
	
	def with_type(self, parameter_type : type) -> Self:
		assert type(parameter_type) is type
		self.type = parameter_type
		return self
	
	def with_validation(self, validator : Callable[[object], bool]) -> Self:
		assert isinstance((validator, callable))
		self.validator = validator
		return self
	
	def with_description(self, description : str) -> Self:
		assert isinstance((description, str))
		self.desc = description
		return self
	

class Optional(Parameter):
	def __init__(self, name : str, short_name : str = None):
		super().__init__(name)
		self.short = short_name
		self.type = bool

	def with_default(self, default : object) -> Self:
		self.default = default
		return self
	

class Output:
	def returns_value(self, value : object) -> Self:
		self.value = value
		return self
	
	def returns_text(self, source : Callable[..., str], **kwargs) -> Self:
		assert isinstance(source, callable)
		self.text_source = source, kwargs
		return self
	