from io import StringIO
import io
import sys
import keyboard	#type: ignore
from typing import Literal, TextIO
import os
from process import Executioner, Parser, STException, parser, execs

LanguageMode = Literal['py', 'sh', 'st']
_PREFIXES = {'st': '~ ', 'py' : '> ', 'sh' : '! ' }
class ConsoleApp:
	mode : LanguageMode
	_parser : Parser
	_exc : Executioner
	def __init__(self, *args : str, shell : bool = True) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.set_mode('st')
		sys.stdout = self.output
		if shell:
			self.prepare_shell()
			keyboard.hook(self.on_keyEvent)
			self._prepare(_PREFIXES[self.mode])
			while True:
				keyboard.wait()

	def prepare_shell(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		print('\n' * os.get_terminal_size().lines)

	def set_mode(self, mode : LanguageMode):
		match mode:
			case 'py':
				self._parser = parser.PythonParser()
				self._exc = execs.PythonExcecutioner({})
			case 'sh':
				self._parser = parser.ShellParser()
				self._exc = execs.ShellExecutioner({})
			case 'st':
				self._parser = parser.StartrakParser()
				self._exc = execs.StartrakExecutioner({})
		self.mode = mode

	def _prepare(self, prompt):
		self.output.write(prompt)
		input_text = self.input.getvalue()
		self.output.write(input_text)
		self.output.flush()
	
	def on_keyEvent(self, key):
		prompt = _PREFIXES[self.mode]
		input_text = self.input.getvalue()
		if key.event_type == 'down':
			if len(key.name) == 1:
				self.input.write(key.name)
				if (key.name == '>' or key.name == '!') and len(input_text.strip()) == 0:
					if key.name == '>':
						self.set_mode('py')
					elif key.name == '!':
						self.set_mode('sh')

					self.output.write('\r' + ' ' * len(prompt + input_text)) 
					self.input.clear()
					self.output.write('\n')
					self._prepare(_PREFIXES[self.mode])
					return
			else:
				if key.name == 'space':
					self.input.write(' ')
				elif key.name == 'backspace':
					self.input.seek(0, io.SEEK_END) 
					self.input.truncate(max(0, self.input.tell() - 1))
					self.input.flush()
				elif key.name == 'enter':
					output = self.input.getvalue()
					self.input.clear()
					self.output.write('\n') 
					self.process(output)
					self._prepare(_PREFIXES[self.mode])
					return
			self.output.write('\r' + ' ' * len(prompt + input_text)) 
			input_text = self.input.getvalue() 
			self.output.write('\r' + prompt + input_text) 

	def process(self, string : str):
		try:
			data = self._parser.parse(string)
			out = self._exc.execute(data)
			print(out)
		except STException as e:
			print('Error:', e)
		except Exception as e:
			print('Python Error:', e)
		if self.mode != 'st':
			self.set_mode('st')

class ConsoleInput(StringIO):
	def __init__(self) -> None:
		super().__init__()
	def clear(self):
		self.truncate(0)
		self.seek(0)
		self.flush()
	
class ConsoleOutput(StringIO):
	def __init__(self, stdout : TextIO) -> None:
		super().__init__()
		self.stdout = stdout

	def write(self, __s: str) -> int:
		self.stdout.write(__s)
		return super().write(__s)
	def flush(self) -> None:
		self.stdout.flush()
		return super().flush()
	
app = ConsoleApp()