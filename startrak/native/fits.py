from mmap import ACCESS_READ, ALLOCATIONGRANULARITY, mmap
from typing import Any, Final, Iterator, TypeVar, Tuple, overload
from startrak.native.alias import ValueType, RealDType
from numpy.typing import NDArray
import numpy as np
_BitDepth =  TypeVar('_BitDepth', bound= np.dtype)

class _FITSBufferedReaderWrapper:
	_filePath : str
	_OFFSET : Final[int] = 2880 << 1

	def __init__(self, file_path : str) -> None:
		self._filePath = file_path

	def _read_header(self) -> Iterator[Tuple[str, ValueType]]:
		_bio = open(self._filePath, 'rb')
		_mmap = mmap(_bio.fileno(), _FITSBufferedReaderWrapper._OFFSET, access=ACCESS_READ)
		while True:
			line = _mmap.read(80)
			if not line: break
			if line[:3] == b'END':
				break

			if not _validate_byteline(line): continue
			_keyword = line[:8].decode()
			_value = _parse_bytevalue(line)
			yield _keyword, _value
		_mmap.close()
		_bio.close()
	@overload
	def _read_data(self,) -> NDArray[np.uint16]: ...
	@overload
	def _read_data(self, dtype :_BitDepth, count : int) -> np.ndarray[Any,_BitDepth]: ...

	def _read_data(self, dtype = np.uint16, count = -1) -> np.ndarray[Any,  _BitDepth]:
		_bio = open(self._filePath, 'rb')
		_offset = (_FITSBufferedReaderWrapper._OFFSET // ALLOCATIONGRANULARITY) * ALLOCATIONGRANULARITY
		_mmap = mmap(_bio.fileno(), 0, offset=_offset, access=ACCESS_READ)
		if _offset == 0:
			_mmap.seek(_FITSBufferedReaderWrapper._OFFSET)
		else:
			_mmap.seek(_FITSBufferedReaderWrapper._OFFSET - _offset)
		data =  np.frombuffer( _mmap.read(), count=count ,dtype=dtype)
		_mmap.close()
		_bio.close()
		return data

def _parse_bytevalue(src : bytes) -> ValueType:
	if src[10] == 39:
		end = src.rfind(39, 19)
		return src[11:end].decode()
	if src[29] == 84 or src[29] == 70:
		return src[29] == 84
	num = float(src[10:30])
	if num.is_integer():
		return int(num)
	return num

def _validate_byteline(line : bytes):
	''' This method returns False when the line is blank or it is a valid line but it contains no data.
	In case of being invalid an OSError exception is thrown, otherwise it returns True'''
	if line == b' '* 80: return False
	if not (line[8] == 61 and line[9] == 32):
		raise IOError('Invalid header syntax', line)
	return True

def _bitsize(depth : int) -> np.dtype[RealDType]:
	if depth == 8: return np.dtype(np.uint8)
	elif depth == 16: return np.dtype(np.uint16)
	elif depth == 32: return np.dtype(np.uint32)
	elif depth == 64: return np.dtype(np.uint64)
	elif depth == -32: return np.dtype(np.float32)
	elif depth == 64: return np.dtype(np.float64)
	else: raise TypeError('Invalid bit depth: ', depth)