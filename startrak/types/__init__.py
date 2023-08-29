from functools import lru_cache
from typing import Any, Callable, ClassVar, Dict, Final, Generic, Iterator, List, Optional, Self, Tuple, Type, TypeVar, cast
from abc import ABC, abstractmethod
import numpy as np
from dataclasses import  dataclass
import os.path
from startrak.types.alias import ImageLike, NumberLike, ValueType, Position, NDArray
from startrak.types.fits import _FITSBufferedReaderWrapper as FITSReader
from startrak.types.fits import _bitsize

_defaults : Final[Dict[str, Type[ValueType]]] = \
		{'SIMPLE' : int, 'BITPIX' : int, 'NAXIS' : int, 'EXPTIME' : float, 'BSCALE' : float, 'BZERO' : float}

class Header():
	_items : Dict[str, ValueType]
	bitsize : np.dtype[NumberLike]
	shape : Tuple[int, int]
	bscale : np.uint
	bzero : np.uint
	def __init__(self, source : Dict[str, ValueType]):
		self._items = {str(key) : value for key, value in  source.items() 
			if type(value) in (int, bool, float, str)}
		if not all((key in self._items for key in _defaults.keys())):
			raise KeyError('Header not having mandatory keywords')
		self.bitsize = _bitsize(cast(int, self._items['BITPIX']))
		self.bscale = cast(np.uint,self._items['BSCALE'])
		self.bzero = cast(np.uint,self._items['BZERO'])
		
		# todo: Add support for ND Arrays
		if self._items['NAXIS'] != 2:
			raise NotImplementedError('Only 2D data blocks are supported')
		self.shape = cast(int, self._items['NAXIS2']),cast(int, self._items['NAXIS1'])
	def contains_key(self, key : str):
		return key in self._items.keys()
	def __getitem__(self, key : str):
		return self._items[key]
	def __getattr__(self, __name: str):
		return self._items[__name]
	def __repr__(self) -> str:
		return '\n'.join([f'{k} = {v}' for k,v in self._items.items()])

class HeaderArchetype(Header):
	_entries : ClassVar[Dict[str, Type[ValueType]]] = {}

	def __init__(self, source : Header | Dict[str, ValueType]):
		self._items = dict()
		for key, _type in _defaults.items():
			self._items[key] = _type(source[key])
		
		for key, _type in HeaderArchetype._entries.items():
			self._items[key] = _type(source[key])
		
		assert 'NAXIS' in self._items
		_naxis = self._items['NAXIS']
		assert type(_naxis) is int
		_naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(_naxis))
		for n in range(_naxis): self._items[f'NAXIS{n+1}'] = _naxisn[n]
	
	def validate(self, header : Header, failed : Optional[Callable[[str, ValueType, ValueType], None]] = None) -> bool:
		for key, value in self._items.items():
			if (key not in header._items.keys()) or (header._items[key] != value):
					if callable(failed): failed(key, value, header._items[key])
					return False
		return True

	@staticmethod
	def set_keywords(user_keys : Dict[str, type]):
		assert all([ type(key) is str  for key in user_keys])
		assert all([ value in (int, bool, float, str) for value in user_keys.values()])
		HeaderArchetype._entries = user_keys

@dataclass
class FileInfo():
	path : Final[str]
	size : Final[int]
	_file : FITSReader
	__header : Header | None

	def __init__(self, path : str):
		assert path.lower().endswith(('.fit', '.fits')),\
			'Input path is not a FITS file'
		self._file = FITSReader(path)
		self.path = os.path.abspath(path)
		self.size = os.path.getsize(path)
		self.__header = None

	@property
	def header(self) -> Header:
		if self.__header is None:
			_dict = {key.rstrip() : value for key, value in self._file._read_header()}
			self.__header = Header(_dict)
		return self.__header
	
	@lru_cache(maxsize=5)	# todo: Add parameter to config
	def get_data(self, scale = True) -> np.ndarray[Any, np.dtype[NumberLike]]:
		_dtype = self.header.bitsize
		_shape = self.header.shape
		_raw = self._file._read_data(_dtype.newbyteorder('>'), _shape[0] * _shape[1])
		if scale:
			_scale, _zero = self.header.bscale, self.header.bzero
			if _scale != 1 or _zero != 0:
				_raw = _zero + _scale * _raw
		return _raw.reshape(_shape).astype(_dtype)
	
	def __setattr__(self, __name: str, __value) -> None:
		raise AttributeError(name= __name)
	def __repr__(self):
		return f'\n{type(self).__name__}(path={os.path.basename(self.path)}, size={self.size} bytes)'
	def __eq__(self, __value):
		if not  isinstance(__value, type(self)): return False
		return self.path == __value.path
	def __hash__(self) -> int:
		return hash(self.path)

@dataclass
class Star():
	name : str
	position : Position
	aperture : int
	
	def __iter__(self) -> Iterator[Position | ValueType]:
		params : List[Position | ValueType] = [type(self).__name__, self.name, self.position, self.aperture]
		yield from params
	
	@classmethod
	def From(cls : Type[Self], other : Star) -> Self:	#type:ignore
		import inspect
		_, *params = other
		_n = len(inspect.signature(cls.__init__).parameters)
		return cls(*params[:_n - 1])	#type: ignore

@dataclass
class ReferenceStar(Star):
	magnitude : float = 0
	def __iter__(self) -> Iterator[Position | ValueType]:
		yield from super().__iter__()
		yield self.magnitude

# ----------------- Tracking ------------------

@dataclass(frozen=True)
class TrackingModel:
	dx : float
	dy : float
	da : float
	
	@classmethod
	def identity(cls) -> Self:
		return cls(0, 0, 0)
	@property
	def matrix(self) -> np.matrix:
		_cos = np.cos(self.da)
		_sin = np.sin(self.da)
		return np.matrix([[_cos, -_sin, self.dx], 
								[_sin, _cos,   self.dy],
								[0,     0,       1   ]])
	@property
	def translation(self) -> np.ndarray:
		return np.array((self.dx, self.dy))
	
	@property
	def rotation(self) -> float:
		return np.degrees(self.da)

# State machine class
_TrackingMethod = TypeVar('_TrackingMethod')
class Tracker(ABC, Generic[_TrackingMethod]):
	_current : _TrackingMethod | None
	_previous : _TrackingMethod | None
	_model : _TrackingMethod | None
	@abstractmethod
	def setup_model(self, stars : List[Star], *args: Tuple):
		pass
	@abstractmethod
	def track(self, images : Iterator[ImageLike]) -> TrackingModel:
		pass