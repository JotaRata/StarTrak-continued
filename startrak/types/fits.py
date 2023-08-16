from dataclasses import dataclass
from io import BufferedReader
from typing import BinaryIO, ClassVar, Dict, Final, Generator, Iterator, Type, Union, Tuple, cast
import numpy as np
from numpy.typing import NDArray
_ValueType = Union[int, float, str, bool]
import os.path

class _FITSBufferedReaderWrapper:
	_file : BinaryIO
	_end_offset : int

	def __init__(self, file_path : str | bytes) -> None:
		self._file = open(file_path, 'rb')
		self._end_offset = 0

	def _read_header(self) -> Iterator[Tuple[str, _ValueType]]:
		while True:
			line = self._file.read(80)
			if not line: break
			if b'END' in line:
				self._end_offset = self._file.tell()
				break
			_validate_byteline(line)
			_keyword = line[:8].decode().rstrip()
			_value = _parse_bytevalue(line)
			yield _keyword, _value
	
	def tell(self):
		return self._file.tell()
	def close(self):
		return self._file.close()
			
def _parse_bytevalue(src : bytes) -> _ValueType:
	if src[10] == 39:
		end = src.rfind(39, 19)
		return src[11:end].decode()
	if src[29] == 84 or src[29] == 66:
		return src[29] == 84
	line = src[10:30].decode()
	num = float(line)
	if num.is_integer():
		return int(num)
	return num

def _validate_byteline(line : bytes):
	if not (line[8] == 61 and line[9] == 32):
		raise IOError('Invalid header syntax')
