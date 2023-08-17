from typing import Any, Callable, ClassVar, Dict, Final, Generator, Optional, Self, Tuple, Type, cast
from abc import ABC, abstractmethod
import numpy as np
from numpy.typing import NDArray
from dataclasses import  dataclass
import os.path
from startrak.types.fits import _FITSBufferedReaderWrapper as BufferedReader
from startrak.types.fits import _ValueType, _bitsize, DTypeLike

_defaults : Final[Dict[str, Type[_ValueType]]] = \
		{'SIMPLE' : int, 'BITPIX' : int, 'NAXIS' : int, 'EXPTIME' : float}
class Header():
	_items : Dict[str, _ValueType]
	bitsize : np.dtype[Any]
	shape : Tuple[int, int]
	def __init__(self, source : Dict[str, _ValueType]):
		self._items = {str(key) : value for key, value in  source.items() 
			if type(value) in (int, bool, float, str)}
		if not all((key in self._items for key in _defaults.keys())):
			raise KeyError('Header not having mandatory keywords')
		self.bitsize = _bitsize(cast(int, self._items['BITPIX']))
		
		# todo: Add support for ND Arrays
		if self._items['NAXIS'] != 2:
			raise NotImplementedError('Only 2D data blocks are supported')
		self.shape = (cast(int, self._items['NAXIS2']),
							cast(int, self._items['NAXIS1']))
	def contains_key(self, key : str):
		return key in self._items.keys()
	def __getitem__(self, key : str):
		return self._items[key]
	def __getattr__(self, __name: str):
		return self._items[__name]
	def __repr__(self) -> str:
		return '\n'.join([f'{k} = {v}' for k,v in self._items.items()])

class HeaderArchetype(Header):
	_entries : ClassVar[Dict[str, Type[_ValueType]]] = {}

	def __init__(self, source : Header | Dict[str, _ValueType]):
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
	
	def validate(self, header : Header, failed : Optional[Callable[[str, _ValueType, _ValueType], None]] = None) -> bool:
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
	_file : BufferedReader
	path : Final[str]
	size : Final[int]
	header : Final[Header]

	def __init__(self, path : str):
		assert path.lower().endswith(('.fit', '.fits')),\
			'Input path is not a FITS file'
		self._file = BufferedReader(path)
		self.path = os.path.abspath(path)
		self.size = os.path.getsize(path)

		self.header = self._build_header()
		self._file.close()

	def _build_header(self):
		_header_dict = {key : value for key, value\
							in self._file._read_header()}
		return Header(_header_dict)

	def __setattr__(self, __name: str, __value) -> None:
		raise AttributeError(name= __name)
	def get_data(self) -> NDArray[np.int_]:
		_dtype = self.header.bitsize
		_shape = self.header.shape
		_raw = self._file._read_data(_dtype, _shape[0] * _shape[1])
		self._file.close()
		return _raw.reshape(_shape)
	
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
	position : Tuple[int, int]
	aperture : int
	
	def __iter__(self):
		return iter((type(self).__name__, self.name, self.position, self.aperture))
	
	@classmethod
	def From(cls : Type[Self], other : Star) -> Self:	#type:ignore
		_, *params = [ *other]
		return cls(*params)

@dataclass
class ReferenceStar(Star):
	magnitude : float = 0
	def __iter__(self):
		yield from super().__iter__()
		yield self.magnitude

class TrackingMethod(ABC):
	@abstractmethod
	def setup_model(self, *args : Tuple[Any, ...]):
		pass
	@abstractmethod
	def track(self):
		pass