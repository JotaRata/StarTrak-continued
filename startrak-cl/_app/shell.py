from .consoleapp import ConsoleApp, _PREFIXES
import keyboard
import os

class ShellConsole(ConsoleApp):
	def __init__(self, *args: str) -> None:
		super().__init__(*args)
		self._prepare_shell()
		keyboard.hook(self.on_keyEvent, suppress= False)
		self._prepare_line(_PREFIXES[self.mode])
		while True:
			keyboard.wait()
	
	def _prepare_shell(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		self.output.write('\n' * os.get_terminal_size().lines)
	
	def _prepare_line(self, prompt):
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
					self._prepare_line(_PREFIXES[self.mode])
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
					self._prepare_line(_PREFIXES[self.mode])
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