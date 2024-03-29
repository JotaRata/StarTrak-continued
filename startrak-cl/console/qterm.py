from typing import Callable
from console.consoleapp import ConsoleApp


class QTerminal(ConsoleApp):
	def __init__(self, *args: str, write_event : Callable) -> None:
		super().__init__(*args)
		self.write_event = write_event

	def write(self, __s: str):
		r = super().write(__s)
		if self.write_event:
			self.write_event()
		return r