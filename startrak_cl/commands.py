from __future__ import annotations
from typing import Any, Callable, Self
from packaging.version import Version

__all__ = ['Command', 'Parameter', 'Optional']

class _AbstractCommandMeta(type):
	registered_commands : dict[str, type] = {}

	def __new__(cls, class_name : str, bases : tuple[type,...], namespace : dict[str, Any], *,
					alias : str = None, 
					description : str = None, 
					author : str = None, 
					version : str = '1.0.0'):
		
		klass : type = super().__new__(cls, class_name, bases, namespace) 
		if class_name == 'Command':
			return klass
		
		assert alias, 'Command requires one parameter "alias"'
		assert description, 'Command requires one parameter "description"'
		assert 'init_params' in namespace, 'Command requires defining an "init_params" method'
		assert 'execute' in namespace, 'Command requires defining an "execute" method'

		assert '__init__' not in namespace, 'Cannot override "__init__" method from Command.'
		assert '__init_subclass__' not in namespace, 'Cannot override "__init_subclass__" method from Command.'

		klass.__alias__ = alias
		klass.__desc__ = description
		klass.__author__ = author
		klass.__version__ = Version(version)

		print(f'Registered command "{alias}" from {klass}')
		_AbstractCommandMeta.registered_commands[klass.__alias__] = klass
		return klass
	
class Command(metaclass= _AbstractCommandMeta):
	def __init__(self):
		raise TypeError(f'Cannot instantiate object of type "{type(self).__name__}"')
	
	def __init_subclass__(cls):
		if cls.__base__ != Command:
			raise TypeError(f'Cannot derive from class "{cls.__base__.__name__}"')
		
	@classmethod
	def get_name(cls) -> str:
		return cls.__alias__
	
	def init_params() -> list[Parameter]:
		raise NotImplementedError()

	def execute(*args : tuple[Parameter, ...], **kwargs) -> None:
		raise NotImplementedError()


class Parameter:
	def __init__(self, name : str):
		self._name = name
	
	def with_type(self, parameter_type : type) -> Self:
		assert type(parameter_type) is type
		self._type = parameter_type
		return self
	
	def with_mapping(self, map : Callable[[str], object]) -> Self:
		assert callable(map)
		self._map = map
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
	def __init__(self, name : str, short_name : str = None, implicit : bool = False):
		super().__init__(name)
		self._short = short_name
		self._imp = implicit
		self._type = bool
		self._default = None

	def with_default(self, default : object) -> Self:
		self._default = default
		return self
	