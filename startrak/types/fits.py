from typing import Any, BinaryIO, Iterator, Type, TypeVar, Union, Tuple, overload
from numpy.typing import NDArray, DTypeLike
import numpy as np

_ValueType = Union[int, float, str, bool]
_BitDepth =  TypeVar('_BitDepth', bound= np.dtype)
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
	@overload
	def _read_data(self,) -> NDArray[np.uint16]: ...
	@overload
	def _read_data(self, dtype : _BitDepth, count : int) -> np.ndarray[Any, _BitDepth]: ...

	def _read_data(self, dtype = np.uint16, count = -1) -> np.ndarray[Any, _BitDepth]:
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
	def closed(self) -> bool:
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

def _bitsize(depth : int) -> np.dtype[Any]:
	if depth == 8: return np.dtype(np.uint8)
	elif depth == 16: return np.dtype(np.uint16)
	elif depth == 32: return np.dtype(np.uint32)
	elif depth == 64: return np.dtype(np.uint64)
	elif depth == -32: return np.dtype(np.float32)
	elif depth == 64: return np.dtype(np.float64)
	else: raise TypeError('Invalid bit depth: ', depth)