from __future__ import annotations
from io import StringIO
from typing import TYPE_CHECKING, Any, Callable, Self
from packaging.version import Version

if TYPE_CHECKING:
	from startrak_cl import ConsoleApp
from startrak_cl import STException

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
	
	def init_params() -> list[ParameterBase]:
		raise NotImplementedError()

	def execute(**kwargs) -> None:
		raise NotImplementedError()

class ParameterBase:
	def __init__(self, name : str):
		if type(self) is ParameterBase:
			raise TypeError('Cannot instantiate class ParameterBase')
		self.name = name

	def with_description(self, description : str) -> Self:
		assert isinstance(description, str)
		self.description = description
		return self

class Parameter(ParameterBase):
	def __init__(self, name : str):
		super().__init__(name)
	
	def with_type(self, parameter_type : type | callable) -> Self:
		assert type(parameter_type) is type or callable(parameter_type)
		self.type_cast = parameter_type
		return self
	
	def with_mapping(self, map : Callable[[str], object]) -> Self:
		assert callable(map)
		self.map_function = map
		return self
	
	def with_validation(self, validator : Callable[[object], bool]) -> Self:
		assert callable(validator)
		self.validate_function = validator
		return self
	

class Optional(Parameter):
	def __init__(self, name : str, short_name : str = None, 
			implicit : bool = False, short_only : bool = False):
		super().__init__(name)

		if short_only and not short_name:
			raise ValueError('Parameters marked as "short_only" must define a short name.')
		self.short_name = short_name
		self.short_only = short_only
		self.is_implicit = implicit
		self.type_cast = bool
		self.default_value = None


	def with_default(self, default : object) -> Self:
		self.default_value = default
		return self
	
class Subcommand(ParameterBase):
	def __init__(self, name : str, implicit= True):
		super().__init__(name)
		self.implicit = implicit
	
	def with_parameters(self, params : list[ParameterBase]):
		self.parameters = params
		return self

	def executes(self, method : Callable):
		self.method = method
		return self

	def get_name(self):
		return self.name


	
class ConsoleHelper:
	def __init__(self, console : ConsoleApp) -> None:
		self._get_size = console.size
		self._get_name = lambda: getattr(type(console), '__name__', 'NULL')
		self.execute = console.process
		self.format = console.format
		self.remove_format = console.remove_format
		self.clear = console.clear
		self.write = console.write
		self.flush = console.flush
	@property
	def width(self) -> int:
		return self._get_size()[1] - 1
	@property
	def height(self) -> int:
		return self._get_size()[0]
	@property
	def name(self) -> str:
		return self._get_name()
	def buffer(self, *args):
		return StringIO(*args)
	
def get_active_console() -> ConsoleHelper:
		try:
			import startrak_cl._globals as GLOBALS
			return ConsoleHelper(GLOBALS.CONSOLE_INSTANCE)
		except:
			raise 


class _HelpCommand(Command,
					alias = 'help',
					description = 'Prints help for the provided command.',
					author = 'JotaRata'):

	def init_params():
		return [
			Parameter('command')
				.with_type(str)
		]
	
	def execute(command, **kwargs):
		cmd = _AbstractCommandMeta.registered_commands.get(command, None)
		console = get_active_console()

		if not cmd:
			raise STException(f'Invalid command: "{command}".')
		
		console.write(console.format(f'Showing help for command: "{command}"'.center(console.width), 'highlight'))
		console.write('\n\n')

		console.write(console.format('DESCRIPTION', 'bold') + '\n')
		console.write(cmd.__desc__)
		console.write('\n\n')

		console.write(console.format('USAGE', 'bold') + '\n ')
		console.write(command)

		parameters = cmd.init_params()
		for param in parameters:
			if type(param) is Parameter or type(param) is Subcommand:
				console.write(f' [{param.name.upper()}')
				if hasattr(param, 'type_cast'):
					console.write(f':{param.type_cast.__name__}')
				console.write(']')

			if type(param) is Optional:
				if param.is_implicit:
					console.write(' ' + console.format(param.name.upper(), 'italic'))
				elif not param.short_only:
					console.write(f' --{param.name}')
				elif param.short_name:
					console.write(f' -{param.short_name}')

				if hasattr(param, 'type_cast'):
					console.write(f':{param.type_cast.__name__}')
		console.write('\n\n')

		console.write(console.format('PARAMETERS', 'bold') + '\n')

		for param in parameters:
			name = ''
			if type(param) is Parameter or type(param) is Subcommand or (type(param) is Optional and param.is_implicit):
				name = f'  {param.name.upper()}'
			elif type(param) is Optional:
				if not param.short_only:
					name = f'  --{param.name}'
				if param.short_name:
					name += f'  -{param.short_name}'
			console.write(name.ljust(console.width // 5))

			desc_has_period = False
			if hasattr(param, 'description'):
				console.write(param.description)
				desc_has_period = param.description.rstrip().endswith('.')
			if not desc_has_period:
				console.write('.')

			console.write('\n')
		console.write('\n')

		console.write(console.format('VERSION', 'bold') + '\n')
		console.write(f' {cmd.__version__}')
		console.write('\n\n')

		console.write(console.format('AUTHORS', 'bold') + '\n')
		console.write(f' {cmd.__author__}')
		console.write('\n\n')
