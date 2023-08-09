from abc import ABC, abstractmethod
import numpy as np
from numpy.typing import NDArray
from astropy.io import fits as _astropy # type: ignore
from dataclasses import FrozenInstanceError, dataclass
import os.path
from typing import Any, Callable, ClassVar, Dict, Generator, Optional, Self, Tuple, Type, Union, cast

_TVal = Union[int, bool, float, str]

class Header():
	_items : Dict[str, _TVal]
	def __init__(self, source : _astropy.Header | Dict[str, _TVal]):
		header_items = cast(Generator[Tuple[str, _TVal], None, None], source.items())
		self._items = {str(key) : value for key, value in header_items 
			if type(value) in (int, bool, float, str)}
	
	def contains_key(self, key : str):
		return key in self._items.keys()
	def __getitem__(self, key : str):
		return self._items[key]
	def __getattr__(self, __name: str):
		return self._items[__name]
	def __repr__(self) -> str:
		return '\n'.join([f'{k} = {v}' for k,v in self._items.items()])

class HeaderArchetype(Header):
	_defaults : ClassVar[Dict[str, Type[_TVal]]] = {'SIMPLE' : int, 'BITPIX' : int,
																		'NAXIS' : int, 'EXPTIME' : float}
	_entries : ClassVar[Dict[str, Type[_TVal]]] = {}

	def __init__(self, source : Header | Dict[str, _TVal]):
		self._items = dict()
		for key, _type in HeaderArchetype._defaults.items():
			self._items[key] = _type(source[key])
		
		for key, _type in HeaderArchetype._entries.items():
			self._items[key] = _type(source[key])
		
		assert 'NAXIS' in self._items
		_naxis = self._items['NAXIS']
		assert type(_naxis) is int
		_naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(_naxis))
		for n in range(_naxis): self._items[f'NAXIS{n+1}'] = _naxisn[n]
	
	def validate(self, header : Header, failed : Optional[Callable[[str, _TVal, _TVal], None]] = None) -> bool:
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

class FileInfo():
	path : str
	size : int
	header : Header
	def __init__(self, source : str | _astropy.HDUList):
		if type(path := source) is str:
			with _astropy.open(path) as hdu:
				assert type(hdu) is _astropy.HDUList
				self.path = os.path.abspath(path)
				self.size = os.path.getsize(path)
				assert isinstance(phdu := hdu[0], _astropy.PrimaryHDU)
				self.header = Header(cast(_astropy.Header, phdu.header))
		elif type(hdu := source) is _astropy.HDUList:
				self.path = os.path.abspath(cast(str, hdu.filename()))
				self.size = os.path.getsize(self.path)
				assert isinstance(phdu := hdu[0], _astropy.PrimaryHDU)
				self.header = Header(cast(_astropy.Header, phdu.header))
		else:
			raise TypeError('Expected one argument of type str or HDUList')
	def __setattr__(self, __name: str, __value: Any) -> None:
			raise FrozenInstanceError(type(self).__name__)
	
	def get_data(self) -> NDArray[np.int_]:
		return _astropy.getdata(self.path)
	def __repr__(self):
		return f'\n[File: "{os.path.basename(self.path)}" ({self.size}) bytes]'

@dataclass
class Star():
	name : str
	position : Tuple[int, int]
	aperture : int
	
	@classmethod
	def From(cls, other : Self) -> Self:
		return cls(other.name, other.position, other.aperture)
	def export(self) -> Tuple[_TVal | Tuple[int, int], ...]:
		return type(self).__name__, self.name, self.position, self.aperture
	def __repr__(self):
		return f'{type(self).__name__}: {self.name}'

class ReferenceStar(Star):
	magnitude : float
	def __init__(self, source : Star, magnitude : float):
		super().__init__(source.name, source.position, source.aperture)
		self.magnitude = magnitude
	
	def export(self):
		return (*super().export(), self.magnitude)

class TrackingMethod(ABC):
	@abstractmethod
	def setup_model(self, *args : Tuple[Any, ...]):
		pass
	@abstractmethod
	def track(self):
		pass