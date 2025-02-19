from io import DEFAULT_BUFFER_SIZE, StringIO
from typing import TextIO
from startrak_cl.alias import LanguageMode

class NoStream(StringIO):
	def write(self, __s: str):
		pass
	def flush(self) :
		pass

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
	
	def insert(self, pos: int, text: str):
		current_position = self.tell()
		self.seek(pos)
		remaining_content = self.read()
		self.seek(pos)
		self.write(text)
		self.write(remaining_content)
		self.seek(current_position)

	def clear(self, reset_cursor= True):
		self.truncate(0)
		self.seek(0)
		if reset_cursor: 
			self._lmov = 0
	
class ConsoleOutput(StringIO):
	def __init__(self, stdout : TextIO) -> None:
		super().__init__()
		self._stdout = stdout if stdout else NoStream()
		self._redirect : TextIO = None

	def write(self, __s: str) -> int:
		if (l:=len(__s)) > DEFAULT_BUFFER_SIZE:
			for i in range(0, l, DEFAULT_BUFFER_SIZE):
				_slice = __s[i : i + DEFAULT_BUFFER_SIZE]
				v = self._writeto(_slice)
			return v
		return self._writeto(__s)
	
	def _writeto(self, __s: str):
		if self._redirect and not self._redirect.closed:
			self._redirect.write(__s)
			return
		self._stdout.write(__s)
		return super().write(__s)
	
	def clear(self):
		self.truncate(0)
		self.seek(0)

	def flush(self) -> None:
		self._stdout.flush()
		return super().flush()
	
	def redirect(self, output : TextIO):
		self._redirect = output

	def reset_output(self):
		self._redirect = None