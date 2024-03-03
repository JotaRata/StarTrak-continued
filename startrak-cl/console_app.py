from io import StringIO
import sys
import keyboard
from typing import Literal, TextIO
import os
from process import Executioner, Parser, STException, parser, execs

LanguageMode = Literal['py', 'sh', 'st']
_PREFIXES = {'st': '[ST]: ', 'py' : '[PY]: ', 'sh' : '[SH]: ' }
class ConsoleApp:
	mode : LanguageMode
	_parser : Parser
	_exc : Executioner
	def __init__(self, *args : str, shell : bool = True) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.index = 0
		self.cursor = 0
		self.set_mode('st')
		sys.stdout = self.output
		if shell:
			self.prepare_shell()
			keyboard.hook(self.on_keyEvent, suppress= False)
			self._prepare(_PREFIXES[self.mode])
			while True:
				keyboard.wait()

	def prepare_shell(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		self.output.write('\n' * os.get_terminal_size().lines)

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
		input_text =self.input.getvalue()
		self.output.write(input_text)
		self.output.flush()
	
	def on_keyEvent(self, key : keyboard.KeyboardEvent):
		input_text = self.input.getvalue()

		def clear_newline():
			prompt = _PREFIXES[self.mode]
			new_text = self.input.get_text() 
			self.output.write('\r' + ' ' * len(prompt + input_text) + '\r' + (prompt + new_text)) 
			self.output.flush()

		if key.event_type == 'down':
			if len(key.name) == 1:
				if (key.name == '>' or key.name == '!') and len(input_text.strip()) == 0:
					if key.name == '>':
						self.set_mode('py')
					elif key.name == '!':
						self.set_mode('sh')
					self.input.clear()
					self.output.write('\r' + ' ' * len(input_text)) 
					self._prepare(_PREFIXES[self.mode])
					return
				else:
					self.input.insert(self.cursor, key.name)
					self.cursor += 1

			else:
				if key.scan_code in keyboard.key_to_scan_codes('space'):
					self.input.insert(self.cursor, ' ')
					self.cursor += 1
				elif key.scan_code in keyboard.key_to_scan_codes('backspace'):
					if self.cursor > 0:
						text = self.input.getvalue()
						current = text[:self.cursor - 1] + text[self.cursor:]
						self.input.clear()
						self.input.write(current)
						self.cursor -= 1
				elif key.scan_code in keyboard.key_to_scan_codes('delete'):
					if self.cursor < len(self.input.getvalue()):
						text = self.input.getvalue()
						current = text[:self.cursor] + text[self.cursor + 1:]
						self.input.shift_left(-1)
						self.input.clear()
						self.input.write(current)

				elif key.scan_code in keyboard.key_to_scan_codes('enter'):
					output = self.input.getvalue()
					self.input.save_state(self.mode)
					self.input.clear()
					self.index = 0
					self.cursor = 0
					self.output.write('\n') 
					self.process(output)
					self._prepare(_PREFIXES[self.mode])
					return
			
			if key.scan_code in keyboard.key_to_scan_codes('up'):
				self.index, self.cursor, mode = self.input.retrieve_state(self.index + 1)
				self.set_mode(mode)
				clear_newline()
				return

			if key.scan_code in keyboard.key_to_scan_codes('down'):
				self.index, self.cursor, mode = self.input.retrieve_state(self.index - 1)
				self.set_mode(mode)
				clear_newline()
				return

			if key.scan_code in keyboard.key_to_scan_codes('left'):
				if self.cursor > 0:
					self.input.shift_left(1)
					self.cursor -= 1

			if key.scan_code in keyboard.key_to_scan_codes('right'):
				if self.cursor < len(input_text): 
					self.input.shift_left(-1)
					self.cursor += 1
			clear_newline()

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

def normalize(s : str):
	return s.replace('\033[D', '').replace('\033[C', '')

class ConsoleInput(StringIO):
	def __init__(self) -> None:
		super().__init__()
		self._h = list[tuple[str, LanguageMode]]()
		self._lmov = 0

	def get_text(self) -> str:
		return self.getvalue() + '\033[D' * self._lmov
	def shift_left(self, shift : int):
		self._lmov += shift
	
	def save_state(self, mode : LanguageMode):
		state = self.getvalue()
		if not state:
			return
		self._h.append((state, mode))
		if len(self._h) > 10:
			self._h.pop(0)
	
	def retrieve_state(self, index : int) -> tuple[int, int, LanguageMode]:
		if not self._h:
			return 0, 0, 'st'
		if index <= 0:
			self.clear()
			return 0, 0, 'st'
		if index > len(self._h): index = len(self._h)
		if index <= 1: index = 1
		state, mode = self._h[-index]
		self.clear()
		self.write(state)
		return index, len(state), mode
	
	def insert(self, pos : int, text : str):
		current = self.getvalue()
		if pos < 0:
			pos = 0
		elif pos > len(current):
			pos = len(current)
		new_content = current[:pos] + text + current[pos:]
		self.clear()
		self.write(new_content)

	def clear(self):
		self.truncate(0)
		self.seek(0)
	
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