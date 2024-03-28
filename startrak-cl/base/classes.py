from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Callable, NamedTuple
from processing.protocols import STException
import _globals

class Positional:
	def __init__(self, index, kind) -> None:
		self.index = index
		self.type = kind
class Optional(Positional):
	pass
class Keyword:
	def __init__(self, key, *kinds) -> None:
		self.key = key
		self.types = kinds
		if not self.types:
			self.types = tuple()
class OptionalKeyword:
	def __init__(self, key, kind, default) -> None:
		self.key = key
		self.type = kind
		self.default = default

class TextRetriever:
	def __init__(self, source : Callable[..., str], *args, **kwargs) -> None:
		self.source = source
		self.args = args
		self.kwargs = kwargs
	def __str__(self) -> str:
		if type(self.source) is str:
			return self.source
		return self.source(*self.args, **self.kwargs)
	def __call__(self) -> str:
		return self.__str__()

class ReturnInfo(NamedTuple):
	name : str = None
	text : str | TextRetriever = None
	path : str = None
	obj : object = None
	def __str__(self) -> str:
		return self.name
	def __int__(self) -> str:
		return int(self.obj)


@dataclass
class _CommandInfo:
	name : str
	args : list[Positional | Optional]
	_kws : list[Keyword | OptionalKeyword]
	ref : Callable

	def __post_init__(self):
		if not self.args:
			self.args = []
		if not self._kws:
			self._kws = []
		self.keywords = {k.key: k for k in self._kws}
		self.count_positional = sum(1 for arg in self.args if type(arg) is Positional)
		self.count_optional = sum(1 for arg in self.args if type(arg) is Optional)
		self.count_kws = sum(1 + (len(arg.types) if type(arg) is Keyword else 1) for arg in self._kws)

	def __call__(self, args : list[str], printable= True):
		helper = Helper(self, args, printable)
		retval = self.ref(helper)
		if retval and type(retval) is not ReturnInfo:
			raise STException(f'Invalid return type for "{self.name}"')
		return retval

class Helper:
	def __init__(self, command : _CommandInfo, args : list[str], printable= True) -> None:
		self.console = _globals.CONSOLE_INSTANCE
		self.args = args
		self.command = command
		self.printable = printable
	
	def get_kw(self, arg : str):
		key = self.command.keywords[arg]

		if type(key) is Keyword:
			if arg not in self.args: 
				return False
			if len(self.args) < 1 + len(key.types): 
				return False
			idx = self.args.index(arg)
			if len(key.types) == 0:
				return True
			values = []
			for j, _type in enumerate(key.types, 1):
				next_ = self.args[idx + j]
				try:
					value = _type(next_)
				except Exception as e:
					raise STException(f'Invalid argument type for "{self.command.name}" at position #{j}: {e}')
				values.append(value)
			if len(values) > 1:
				return values
			return value
		
		elif type(key) is OptionalKeyword:
			if arg not in self.args: 
				return False, key.default
			if len(self.args) < 2: 
				return True, key.default
			idx = self.args.index(arg)
			try:
				return True, key.type(self.args[idx + 1])
			except:
				return True, key.default
			
	def get_arg(self, pos : int):
		_type = self.command.args[pos].type
		if pos > len(self.args):
			if type(self.command.args[pos]) is Optional:
					return None
			raise STException(f'Expected argument at position #{pos + 1} of the function "{self.command.name}"')
		if str(self.args[pos]).startswith('-') and type(self.command.args[pos]) is Optional:
			return None
		try:
			value = _type(self.args[pos])
		except IndexError:
			raise STException(f'Parameter index out of range for "{self.command.name}"')
		except:
			raise STException(f'Invalid argument type for "{self.command.name}" at position #{pos + 1}')
		return value
	
	def save_buffer(self):
		self._buffer = self.console.output.getvalue()
	
	def retrieve_buffer(self):
		self.clear_console()
		self.console.output.write(self._buffer)
		del self._buffer

	def clear_console(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		self.console.output.clear()

	def flush_console(self):
		self.console.output.flush()

	def handle_action(self,  prompt : str, callbacks : list[Callable] = []):
		self.console.set_mode('action', callbacks= callbacks)
		self.console.input.clear()
		self.console.output.write(prompt)

	def print(self, source : str | TextRetriever, newline= True):
		if not self.printable:
			return
		n = '\n' if newline else ''
		if type(source) is str:
			self.console.output.write(source + n)
			return
		self.console.output.write(str(source) + n)


def highlighted_text(text):
	highlighted_text = f"\033[1m{text}\033[0m"
	return highlighted_text

def underlined_text(text):
	underlined_text = f"\033[4m{text}\033[0m"
	return underlined_text

def inverse_text(text):
	inverse_text = f"\033[7m{text}\033[0m"
	return inverse_text

def blinking_text(text):
	blinking_text = f"\033[5m{text}\033[0m"
	return blinking_text

_REGISTERED_COMMANDS = dict[str, _CommandInfo]()