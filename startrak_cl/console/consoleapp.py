from contextlib import contextmanager
from io import StringIO
import os
import sys
from startrak_cl import _globals
from typing import Literal
from startrak_cl.processing.protocols import Executor, Parser
from startrak_cl.processing import parsers as parser
from startrak_cl.processing import executors as execs
from startrak_cl.processing.executors import get_command, get_commands
from startrak_cl.alias import InputMode, LanguageMode
from startrak_cl import STException
from startrak_cl.streams import ConsoleInput, ConsoleOutput
from startrak_cl.utils.string_operations import word_index, common_string
import startrak

FormatMode = Literal['highlight', 'underline', 'bold', 'blink', 'red', 'yellow', 'blue', 'green', 'magenta']
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
	
	def size(self):
		return os.get_terminal_size().lines, os.get_terminal_size().columns

	def __init__(self, *args : str) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.index = 0
		self.cursor = 0
		self.set_language('st')
		self.set_mode('text')
		sys.stdout = self.output
		sys.stderr = self.output

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
				self._exc = execs.PythonExecutor(ConsoleApp._globals)
			case 'sh':
				self._parser = parser.ShellParser()
				self._exc = execs.ShellExecutor({})
			case 'st':
				self._parser = parser.StartrakParser()
				self._exc = execs.StartrakExecutor(ConsoleApp._globals)
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
			print('Python Error:', e)
			raise
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

	def complete_name(self, input_text : str):
		if self._language_mode != 'st':
				return False
		possible = []
		if not ' ' in input_text.strip():
			for command in get_commands():
				if command.lower().startswith(input_text.lower()):
					possible.append(command)
		else:
			words, word_idx, _ = word_index(input_text, self.cursor)
			command = get_command(words[0])
			if not command or (words[word_idx].startswith('-') or (words[0]=='add' and words[1]=='star')):
				return False
			
			parameters = command.init_params()
			current_parameter = parameters[word_idx - 1] if word_idx - 1 < len(parameters) else None

			if type(current_parameter).__name__ == 'Subcommand':
				current_parameter = current_parameter.parameters[word_idx - 2]
				
			if type(getattr(current_parameter, 'type_cast', None)).__name__ == 'path':
				scan_path = os.getcwd()
				dir_idx = 0
				curr_index = 0

				if '/' in words[word_idx]:
					dirs, dir_idx, curr_index = word_index(words[word_idx], self.cursor - len(" ".join(words[:word_idx])) - 1, '/')
					new_path = '/'.join(dirs[:-1])
					if os.path.exists(new_path):
						scan_path = new_path

				for path in os.scandir(scan_path):
					if (p:=os.path.basename(path)).lower().startswith(words[word_idx][curr_index:].strip('"').lower()):
						if dir_idx == 0:
							res = f'{" ".join(words[:word_idx])} {p}' if not ' ' in p else f'{command.name} "{p}"' 
						else:
							res = f'{" ".join(words[:word_idx])} {scan_path}/{p}' if not ' ' in p else f'{command.name} {scan_path}/"{p}"' 

						possible.append(res)
		
		if len(possible) > 1:
				self.output.write('\n')
				self.output.write('\n'.join(possible) + '\n'*2)

				common = common_string(possible)
				if common:
					self.input.clear()
					self.input.write(common)
					self.cursor = len(common)
		elif len(possible) == 1:
			self.input.clear()
			self.input.write(possible[0])
			self.cursor = len(possible[0])
		return True

	
	def clear(self):
		self.output.clear()
	def write(self, __s : str):
		return self.output.write(__s)
	def read(self):
		return self.output.getvalue()
	def flush(self):
		return self.output.flush()
	
	@contextmanager
	def redirect_output(self):
		new_output = StringIO()
		self.output.redirect(new_output)
		yield new_output

		self.output.reset_output()
		new_output.close()
	
	def format(self, text : str, format : FormatMode):
		match format:
			case 'highlight':
				return f'[{text}]'
			case _:
				return text
			
	def remove_format(self, text : str):
		return text.strip('[]')