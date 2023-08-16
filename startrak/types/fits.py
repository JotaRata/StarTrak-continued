from typing import BinaryIO, Iterator, Union, Tuple
_ValueType = Union[int, float, str, bool]

class _FITSBufferedReaderWrapper:
	_bio : BinaryIO
	_end_offset : int

	def __init__(self, file_path : str | bytes, offset : int = 0) -> None:
		self._bio = open(file_path, 'rb')
		self._end_offset = offset

	def _read_header(self) -> Iterator[Tuple[str, _ValueType]]:
		while True:
			line = self._bio.read(80)
			if not line: break
			if b'END' in line:
				self._end_offset = self._bio.tell()
				break
			_validate_byteline(line)
			_keyword = line[:8].decode().rstrip()
			_value = _parse_bytevalue(line)
			yield _keyword, _value
	
	def reset(self, offset : int = 0):
		if offset != 0:
			_FITSBufferedReaderWrapper.__init__(self, self._bio.name, offset)
		self._bio.seek(offset)
	def tell(self):
		return self._bio.tell()
	def close(self):
		return self._bio.close()
			
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