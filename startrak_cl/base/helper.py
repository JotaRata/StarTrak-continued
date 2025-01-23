from __future__ import annotations
from dataclasses import dataclass
from io import IOBase
import sys
from typing import TYPE_CHECKING, Callable

@dataclass(frozen= True, slots= True)
class _ReturnValue:
	value : object = None
	text : _TextMethod = None
	path : str = None

class _TextMethod:
	def __init__(self, source : Callable[..., str], *args, **kwargs) -> None:
		self.source = source
		self.args = args
		self.kwargs = kwargs
	def __str__(self) -> str:
		if type(self.source) is str:
			return self.source
		return self.source(*self.args, **self.kwargs)
	def get_str(self) -> str:
		return self.__str__()
	
class _ConsoleOutputContext:
	def __init__(self, buffer : IOBase, close_buffer : bool):
		self._buffer = buffer
		self._stdout = sys.stdout
		self._close = close_buffer
	def write(self, *args):
		return self._buffer.write(*args)
	def read(self, *args):
		return self._buffer.read(*args)
	def seek(self, *args):
		return self._buffer.seek(*args)
	def tell(self, ):
		return self._buffer.tell()
	def __enter__(self):
		sys.stdout = self._buffer
	def __exit__(self, *args):
		sys.stdout = self._stdout
		if self._close:
			self._buffer.close()
