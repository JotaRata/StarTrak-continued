from typing import BinaryIO, Iterator, Type, Union, Tuple

import numpy as np
_ValueType = Union[int, float, str, bool]

class _FITSBufferedReaderWrapper:
	_bio : BinaryIO
	_endPos : int
	_offset : int

	def __init__(self, file_path : str | bytes) -> None:
		self._bio = open(file_path, 'rb')
		self._endPos = 0
		self._offset = 2880 << 1	# account for the extra bit not present in ASCII encoding

	def _read_header(self) -> Iterator[Tuple[str, _ValueType]]:
		if self.closed: self.reset()
		while True:
			line = self._bio.read(80)
			if not line: break
			if b'END' in line:
				self._endPos = self._bio.tell()
				break
			_validate_byteline(line)
			_keyword = line[:8].decode().rstrip()
			_value = _parse_bytevalue(line)
			yield _keyword, _value
	
	def _read_data(self, dtype : Type = np.uint16, count : int = -1):
		if self.closed: self.reset(self._offset)
		data = self._bio.read()
		return np.frombuffer(data, count=count ,dtype=dtype)

	def reset(self, offset : int = 0):
		if offset != 0:
			_FITSBufferedReaderWrapper.__init__(self, self._bio.name)
		self._bio.seek(offset)
	def tell(self):
		return self._bio.tell()
	@property
	def closed(self):
		return self._bio.closed
	def close(self):
		return self._bio.close()
			
def _parse_bytevalue(src : bytes) -> _ValueType:
	if src[10] == 39:
		end = src.rfind(39, 19)
		return src[11:end].decode()
	if src[29] == 84 or src[29] == 66:
		return src[29] == 84
	num = float(src[10:30])
	if num.is_integer():
		return int(num)
	return num

def _validate_byteline(line : bytes):
	if not (line[8] == 61 and line[9] == 32):
		raise IOError('Invalid header syntax')