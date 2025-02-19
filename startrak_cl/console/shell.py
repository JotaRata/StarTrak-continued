from startrak_cl import ConsoleApp, _PREFIXES, FormatMode
from startrak_cl.console import keyboard
import os

class ShellConsole(ConsoleApp):
	FORMATS = {
		'highlight': "\033[7m",
		'italic': "\033[3m",
		'bold': "\033[1m",
		'underline': "\033[4m",
		'blink': "\033[5m",
		'red': "\033[91m",
		'green': "\033[92m",
		'yellow': "\033[93m",
		'cyan': "\033[96m",
		'blue': "\033[94m",
		'purple': "\033[95m",
		'highlight-red': "\033[41m",
		'highlight-green': "\033[42m",
		'highlight-yellow': "\033[43m",
		'highlight-cyan': "\033[46m",
		'highlight-blue': "\033[44m",
		'highlight-purple': "\033[45m"
	}

	END_CODE = '\033[0m'

	def __init__(self, *args: str) -> None:
		super().__init__(*args)
		self._prepare_shell()
		keyboard.add_callback(self.on_keyEvent)
		self._prepare_line(_PREFIXES[self._language_mode])
	
	def _prepare_shell(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		self.output.write('\n' * self.size()[0])
	
	def set_mode(self, mode, **kwargs):
		if mode == 'text':
			self.output.write('\n')
			self._prepare_line(_PREFIXES[self._language_mode])
		return super().set_mode(mode, **kwargs)
	
	def _prepare_line(self, prompt):
		self.output._stdout.write(prompt)
		input_text =self.input.getvalue()
		self.output._stdout.write(input_text)
		self.output.flush()
	
	def on_keyEvent(self, key : str):
		if self._input_mode == 'action':
			self.process_action(key)
			return

		input_text = self.input.getvalue()
		def clear_newline():
			prompt = _PREFIXES[self._language_mode]
			new_text = self.input.get_text() 
			self.output._stdout.write('\r' + ' ' * len(prompt + input_text) + '\r' + (prompt + new_text)) 
			self.output._stdout.flush()

		if len(key) == 1:
			if (key == '>' or key == '!') and len(input_text.strip()) == 0:
				if key == '>':
					self.set_language('py')
				elif key == '!':
					self.set_language('sh')
				self.input.clear()
				self.output._stdout.write('\r' + ' ' * len(input_text)) 
				self._prepare_line(_PREFIXES[self._language_mode])
				return
			else:
				self.input.insert(self.cursor, key)
				self.cursor += 1

		else:
			if key == 'space':
				self.input.insert(self.cursor, ' ')
				self.cursor += 1
			elif key == 'backspace':
				if self.cursor > 0:
					text = self.input.getvalue()
					current = text[:self.cursor - 1] + text[self.cursor:]
					self.input.clear(False)
					self.input.write(current)
					self.cursor -= 1
			elif key == 'del':
				if self.cursor < len(self.input.getvalue()):
					text = self.input.getvalue()
					current = text[:self.cursor] + text[self.cursor + 1:]
					self.input.shift_left(-1)
					self.input.clear(False)
					self.input.write(current)

			elif key == 'enter':
				output = self.input.getvalue()
				self.input.save_state(self._language_mode)
				self.input.clear()
				self.index = 0
				self.cursor = 0
				self.output._stdout.write('\n') 
				self.process(output)
				self._prepare_line(_PREFIXES[self._language_mode])
				return
		
		if key == 'up':
			self.index, self.cursor, mode = self.input.retrieve_state(self.index + 1)
			self.set_language(mode)
			clear_newline()
			return

		if key == 'down':
			self.index, self.cursor, mode = self.input.retrieve_state(self.index - 1)
			self.set_language(mode)
			clear_newline()
			return

		if key == 'left':
			if self.cursor > 0:
				self.input.shift_left(1)
				self.cursor -= 1

		if key == 'right':
			if self.cursor < len(input_text): 
				self.input.shift_left(-1)
				self.cursor += 1
		
		if key == 'tab':
			completed = self.complete_name(input_text)
			if not completed:
				clear_newline()

		clear_newline()

	def clear(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		return super().clear()
	
	def format(self, text: str, format: FormatMode) -> str:
		format_code = ShellConsole.FORMATS.get(format, None)
		if format_code:
			return f"{format_code}{text}{ShellConsole.END_CODE}"
		return text

	def remove_format(self, text):
		for code in ShellConsole.FORMATS.values():
			text = text.replace(code, '')
		return text.replace(ShellConsole.END_CODE, '')