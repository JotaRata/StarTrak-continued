from io import StringIO
import io
import sys
import keyboard	#type:ignore
from typing import Literal, TextIO
import os
from process import Executioner, Parser, STException, parser, execs

LanguageMode = Literal['py', 'sh', 'st']
_INPUT_INTERRUPT_KEY = '!'+str(hash(object()))

class ConsoleApp:
	mode : LanguageMode
	_parser : Parser
	_exc : Executioner
	def __init__(self, *args : str, shell : bool = True) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.set_mode('st')
		sys.stdout = self.output	#type: ignore
		if shell:
			self.prepare_shell()
			self.console_loop()

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

	def console_loop(self):
		prefixes = {'st': '~ ', 'py' : '> ', 'sh' : '!' }
		while True:
			user_input = self.read_input(prefixes[self.mode])
			if user_input == _INPUT_INTERRUPT_KEY:
				continue
			self.process(user_input)

	def read_input(self, prompt=''):
		self.output.write(prompt)  # Print the prompt
		input_text = self.input.getvalue()  # Get the current input text from the buffer
		self.output.write(input_text)  # Print the current input text
		while True:
			key = keyboard.read_event(True)
			if key.event_type == 'down':
					if len(key.name) == 1:
						self.input.write(key.name)
						if (key.name == '>' or key.name == '!') and len(input_text.strip()) == 0:
							if key.name == '>':
								self.set_mode('py')
							elif key.name == '!':
								self.set_mode('sh')

							self.output.write('\r' + ' ' * len(prompt + input_text))  # Clear the line
							self.input.clear()
							self.output.write('\n')
							return _INPUT_INTERRUPT_KEY
					else:
						if key.name == 'space':
							self.input.write(' ')
						elif key.name == 'backspace':
							self.input.seek(0, io.SEEK_END)  # Move to the end of the buffer
							self.input.truncate(max(0, self.input.tell() - 1))
							self.input.flush()
						elif key.name == 'enter':
							break
						
			self.output.write('\r' + ' ' * len(prompt + input_text))  # Clear the line
			input_text = self.input.getvalue()  # Get the updated input text from the buffer
			self.output.write('\r' + prompt + input_text)  # Print the updated input text
		output = self.input.getvalue()
		self.input.clear()
		self.output.write('\n')  # Move to the next line
		return output

	def process(self, string : str):
		data = self._parser.parse(string)

		try:
			out = self._exc.execute(data)
			print(out)
		except STException as e:
			print('Error:', e)
		except Exception as e:
			print('Python Error:', e)

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