from .consoleapp import ConsoleApp, _PREFIXES
from _wrapper import get_command, get_commands
from _utils import word_index, common_string
import keyboard
import os

class ShellConsole(ConsoleApp):
	def __init__(self, *args: str) -> None:
		super().__init__(*args)
		self._prepare_shell()
		keyboard.hook(self.on_keyEvent, suppress= False)
		self._prepare_line(_PREFIXES[self._language_mode])
		keyboard.wait()
	
	def _prepare_shell(self):
		match os.name:
			case 'posix':
				os.system('clear')
			case 'nt' | 'java':
				os.system('cls')
		self.output.write('\n' * os.get_terminal_size().lines)
	
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
	
	def on_keyEvent(self, key : keyboard.KeyboardEvent):
		if self._input_mode == 'action':
			if key.event_type == 'down':
				self.process_action(key.name)
			return

		input_text = self.input.getvalue()
		def clear_newline():
			prompt = _PREFIXES[self._language_mode]
			new_text = self.input.get_text() 
			self.output.write('\r' + ' ' * len(prompt + input_text) + '\r' + (prompt + new_text)) 
			self.output.flush()

		if key.event_type == 'down':
			if len(key.name) == 1:
				if (key.name == '>' or key.name == '!') and len(input_text.strip()) == 0:
					if key.name == '>':
						self.set_language('py')
					elif key.name == '!':
						self.set_language('sh')
					self.input.clear()
					self.output.write('\r' + ' ' * len(input_text)) 
					self._prepare_line(_PREFIXES[self._language_mode])
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
						self.input.clear(False)
						self.input.write(current)
						self.cursor -= 1
				elif key.scan_code in keyboard.key_to_scan_codes('delete'):
					if self.cursor < len(self.input.getvalue()):
						text = self.input.getvalue()
						current = text[:self.cursor] + text[self.cursor + 1:]
						self.input.shift_left(-1)
						self.input.clear(False)
						self.input.write(current)

				elif key.scan_code in keyboard.key_to_scan_codes('enter'):
					output = self.input.getvalue()
					self.input.save_state(self._language_mode)
					self.input.clear()
					self.index = 0
					self.cursor = 0
					self.output.write('\n') 
					self._prepare_line(_PREFIXES[self._language_mode])
					self.process(output)
					return
			
			if key.scan_code in keyboard.key_to_scan_codes('up'):
				self.index, self.cursor, mode = self.input.retrieve_state(self.index + 1)
				self.set_language(mode)
				clear_newline()
				return

			if key.scan_code in keyboard.key_to_scan_codes('down'):
				self.index, self.cursor, mode = self.input.retrieve_state(self.index - 1)
				self.set_language(mode)
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
			
			if key.scan_code in keyboard.key_to_scan_codes('tab'):
				if self._language_mode != 'st':
					clear_newline()
					return
				possible = []
				if not ' ' in input_text.strip():
					for command in get_commands():
						if command.lower().startswith(input_text.lower()):
							possible.append(command)
				else:
					words, word_idx, _ = word_index(input_text, self.cursor)
					command = get_command(words[0])
					if not command or (words[word_idx].startswith('-') or (words[0]=='add' and words[1]=='star')):
						clear_newline()
						return
					if getattr(command.args[word_idx - 1].type, '__name__', None) == 'path':
						scan_path = os.getcwd()
						dir_idx = 0
						curr_indx = 0
						if '/' in words[word_idx]:
							dirs, dir_idx, curr_indx = word_index(words[word_idx], self.cursor - len(" ".join(words[:word_idx])) - 1, '/')
							new_path = '/'.join(dirs[:-1])
							if os.path.exists(new_path):
								scan_path = new_path

						for path in os.scandir(scan_path):
							if (p:=os.path.basename(path)).lower().startswith(words[word_idx][curr_indx:].strip('"').lower()):
								if dir_idx == 0:
									res = f'{" ".join(words[:word_idx])} {p}' if not ' ' in p else f'{command.name} "{p}"' 
								else:
									res = f'{" ".join(words[:word_idx])} {scan_path}/{p}' if not ' ' in p else f'{command.name} {scan_path}/"{p}"' 

								possible.append(res)
				
				if len(possible) > 1:
						self.output.write('\n')
						self.output.write('\n'.join(possible) + '\n')

						common = common_string(possible)
						if common:
							self.input.clear()
							self.input.write(common)
							self.cursor = len(common)
				elif len(possible) == 1:
					self.input.clear()
					self.input.write(possible[0])
					self.cursor = len(possible[0])

			clear_newline()
