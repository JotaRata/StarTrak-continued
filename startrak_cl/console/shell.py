from .consoleapp import ConsoleApp, _PREFIXES, FormatMode
# import keyboard
from console import keyboard
import os

class ShellConsole(ConsoleApp):
	def __init__(self, *args: str) -> None:
		super().__init__(*args)
		self._prepare_shell()
		keyboard.add_callback(self.on_keyEvent)
		self._prepare_line(_PREFIXES[self._language_mode])
	
	def _prepare_shell(self):
		return
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
		self.output.write(prompt)
		input_text =self.input.getvalue()
		self.output.write(input_text)
		self.output.flush()
	
	def on_keyEvent(self, key : str):
		if self._input_mode == 'action':
			self.process_action(key)
			return

		input_text = self.input.getvalue()
		def clear_newline():
			prompt = _PREFIXES[self._language_mode]
			new_text = self.input.get_text() 
			self.output.write('\r' + ' ' * len(prompt + input_text) + '\r' + (prompt + new_text)) 
			self.output.flush()

		if len(key) == 1:
			if (key == '>' or key == '!') and len(input_text.strip()) == 0:
				if key == '>':
					self.set_language('py')
				elif key == '!':
					self.set_language('sh')
				self.input.clear()
				self.output.write('\r' + ' ' * len(input_text)) 
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
				self.output.write('\n') 
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
	
	def format(self, text : str, format : FormatMode) -> str:
		match format:
			case 'highlight':
				return f"\033[7m{text}\033[0m"
			case 'italic':
				return f"\033[3m{text}\033[0m"
			case 'bold':
				return f"\033[1m{text}\033[0m"
			case 'underline':
				return f"\033[4m{text}\033[0m"
			case 'blink':
				return f"\033[5m{text}\033[0m"
			
			case 'red':
				return f"\033[91m{text}\033[0m"
			case 'green':
				return f"\033[92m{text}\033[0m"
			case 'yellow':
				return f"\033[93m{text}\033[0m"
			case 'cyan':
				return f"\033[96m{text}\033[0m"
			case 'blue':
				return f"\033[94m{text}\033[0m"
			case 'purple':
				return f"\033[95m{text}\033[0m"
			
			case 'highlight-red':
				return f"\033[41m{text}\033[0m"
			case 'highlight-green':
				return f"\033[42m{text}\033[0m"
			case 'highlight-yellow':
				return f"\033[43m{text}\033[0m"
			case 'highlight-cyan':
				return f"\033[46m{text}\033[0m"
			case 'highlight-blue':
				return f"\033[44m{text}\033[0m"
			case 'highlight-purple':
				return f"\033[45m{text}\033[0m"
			case _:
				return text