import sys
from time import sleep
from typing import Callable
from _process.protocols import Executor, Parser, STException
from _process import parsers as parser
from _process import executors as execs
from alias import InputMode, LanguageMode
from streams import ConsoleInput, ConsoleOutput
import _globals
import startrak

_PREFIXES = {'st': '[ST]: ', 'py' : '[PY]: ', 'sh' : '[SH]: ' }
class ConsoleApp:
	_language_mode : LanguageMode
	_input_mode : InputMode
	_parser : Parser
	_exc : Executor
	_globals = {var:vars(startrak)[var] for var in dir(startrak) if not var.startswith('_')}

	def __new__(cls, *args, **kwargs):
		if _globals.CONSOLE_INSTANCE is None:
			_globals.CONSOLE_INSTANCE = super().__new__(cls)
		return _globals.CONSOLE_INSTANCE
	
	@classmethod
	def instance(cls):
		return _globals.CONSOLE_INSTANCE

	def __init__(self, *args : str) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.index = 0
		self.cursor = 0
		self.set_language('st')
		self.set_mode('text')
		sys.stdout = self.output

	def set_mode(self, mode : InputMode, **kwargs):
		self.input.clear()

		match mode:
			case 'text':
				if hasattr(self, '_callbacks'):
					del self._callbacks
			case 'action':
				if 'callbacks' in kwargs:
					self._callbacks = kwargs['callbacks']
		self._input_mode = mode

	def set_language(self, mode : LanguageMode):
		match mode:
			case 'py':
				self._parser = parser.PythonParser()
				self._exc = execs.PythonExcecutioner(ConsoleApp._globals)
			case 'sh':
				self._parser = parser.ShellParser()
				self._exc = execs.ShellExecutioner({})
			case 'st':
				self._parser = parser.StartrakParser()
				self._exc = execs.StartrakExecutioner(ConsoleApp._globals)
		self._language_mode = mode

	def process(self, string : str):
		try:
			data = self._parser.parse(string)
			self._exc.execute(data)
		except STException as e:
			print('Error:', e)
			if self._input_mode == 'action':
				self.set_mode('text')
		except Exception as e:
			raise
			print('Python Error:', e)
		if self._language_mode != 'st':
			self.set_language('st')

	def process_action(self, key):
		if not hasattr(self, '_callbacks'):
			return
		exit_flag = True
		for call in self._callbacks:
			flag = call(key)
			if flag is not None:
				exit_flag &= flag
		if exit_flag:
			self.set_mode('text')