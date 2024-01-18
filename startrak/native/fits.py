from __future__ import annotations
from collections import deque
from mmap import ACCESS_READ, ALLOCATIONGRANULARITY, mmap
from re import I
import sys
from typing import Any, Final, Iterator, List, NamedTuple, TypeVar, Tuple, overload
from startrak.native.alias import NDArray, ValueType, RealDType
import numpy as np


_BitDepth =  TypeVar('_BitDepth', bound= np.dtype)
BYTE_OFFSET : Final[int] = 2880 << 1

# DYNAMIC OBJECTS
MAX_CACHED = 5
MAX_ARRAYSIZE = 1048576
_fitsdata_lru = [0] * MAX_CACHED
_fitsdata_cache = dict[int, NDArray]()

def _enqueue_data(id : int, data : NDArray):
	if id in _fitsdata_cache:
		return
	if sys.getsizeof(data) > MAX_ARRAYSIZE:
		print('File too big to cache')
		return
	last = _fitsdata_lru.pop(0)
	if last in _fitsdata_cache:
		del _fitsdata_cache[last]
	_fitsdata_cache[id] = data
	_fitsdata_lru.append(id)

def _get_header(path : str) -> Iterator[Tuple[str, ValueType]]:
	_bio = open(path, 'rb')
	_mmap = mmap(_bio.fileno(), BYTE_OFFSET, access=ACCESS_READ)
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
	
class _bound_reader(NamedTuple):
	path : str
	shape : Tuple[int, int]
	transf : Tuple[int, int]
	dtype : int

	def __call__(self) -> NDArray:
		if (sid := id(self)) in _fitsdata_cache:
			print('found cache', sid)
			return _fitsdata_cache[sid]

		file = open(self.path, 'rb')
		offset = (BYTE_OFFSET // ALLOCATIONGRANULARITY) * ALLOCATIONGRANULARITY
		_mmap = mmap(file.fileno(), 0, offset=offset, access=ACCESS_READ)
		
		_dtype = get_bitsize(self.dtype)
		if offset == 0:
			_mmap.seek(BYTE_OFFSET)
		else:
			_mmap.seek(BYTE_OFFSET - offset)	
		raw =  np.frombuffer( _mmap.read(), count= self.shape[0] * self.shape[1] ,dtype= _dtype.newbyteorder('>'))
		_mmap.close()
		file.close()

		if self.transf[0] > 0:
			_scale, _zero = np.uint(self.transf[0]), np.uint(self.transf[1])
			if _scale != 1 or _zero != 0:
				raw = _zero + _scale * raw
		data = raw.reshape(self.shape).astype(_dtype)

		if MAX_CACHED > 0:
			_enqueue_data(sid, data)
		return data
	def __repr__(self) -> str:
		return object.__repr__(self)

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

def get_bitsize(depth : int) -> np.dtype[RealDType]:
	if depth == 8: return np.dtype(np.uint8)
	elif depth == 16: return np.dtype(np.uint16)
	elif depth == 32: return np.dtype(np.uint32)
	elif depth == 64: return np.dtype(np.uint64)
	elif depth == -32: return np.dtype(np.float32)
	elif depth == 64: return np.dtype(np.float64)
	else: raise TypeError('Invalid bit depth: ', depth)