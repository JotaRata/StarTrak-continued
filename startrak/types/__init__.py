import os.path
from typing import Callable, Dict, Optional, Self, Tuple
from .abstract import Interface
from .abstract import abstract
from astropy.io import fits as _astropy
from numpy import ndarray

__header_allowed_types : Tuple[type, type, type, type]  = (int, bool, float, str)
__archetype_entries : Dict[str, type] = {'SIMPLE' : int, 'BITPIX' : int,
											'NAXIS' : int, 'EXPTIME' : float}
__archetype_user_entries : Dict[str, type] = {}

class Header():
	def __init__(self, source : _astropy.Header | dict):
		self._items = {str(key) : value for key, value in source.items() 
			if type(value) in __header_allowed_types}
	
	def contains_key(self, key : str):
		return key in self._items.keys()
	def __getitem__(self, key : str):
		return self._items[key]
	def __getattr__(self, __name: str):
		return self._items[__name]
	def __repr__(self) -> str:
		return '\n'.join([f'{k} = {v}' for k,v in self._items.items()])

class HeaderArchetype(Header):
	def __init__(self, source : Header | dict):
		self._items = dict()
		for key, _type in __archetype_entries.items():
			self._items[key] = _type(source[key])
		
		for key, _type in __archetype_user_entries.items():
			self._items[key] = _type(source[key])
		
		assert 'NAXIS' in self._items
		_naxis = self._items['NAXIS']
		_naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(_naxis))
		for n in range(_naxis): self._items[f'NAXIS{n+1}'] = _naxisn[n]
	
	def validate(self, header : Header, failed : Optional[Callable] = None) -> bool:
		for key, value in self._items.items():
			if (key not in header._items.keys()) or (header._items[key] != value):
					if callable(failed): failed(key, value, header._items[key])
					return False
		return True

	@staticmethod
	def set_keywords(user_keys : Dict[str, type]):
		assert all([ type(key) is str  for key in user_keys])
		assert all([ value in __header_allowed_types for value in user_keys.values()])
		global __archetype_user_entries
		__archetype_user_entries = user_keys

class FileInfo():
	def __init__(self, *args):
		if len(args) == 1 and type(path := args[0]) is str:
			with _astropy.open(path) as hdu:
				self.path = os.path.abspath(path)
				self.size = os.path.getsize(path)
				phdu = hdu[0]
				assert isinstance(phdu, _astropy.PrimaryHDU)
				self.header = Header(phdu.header)
				return
		elif len(args) == 1 and type(hdu := args[0]) is _astropy.HDUList:
				self.path = os.path.abspath(hdu.filename())
				self.size = os.path.getsize(self.path)
				phdu = hdu[0]
				assert isinstance(phdu, _astropy.PrimaryHDU)
				self.header = Header(phdu.header)
				return
		else:
			raise TypeError('Expected one argument of type str or HDUList')
	
	def get_data(self) -> ndarray:
		return _astropy.getdata(self.path)
	def __repr__(self):
		return f'\n[File: "{os.path.basename(self.path)}" ({self.size}) bytes]'

class Star():
	def __init__(self, name : str, position : Tuple[int, int], aperture : int):
		self.name = name
		assert len(position) == 2
		self.position = position
		self.aperture = aperture
	@classmethod
	def From(cls, other : Self, **kwargs) -> Self:
		return cls(other.name, other.position, other.aperture)
	def export(self) -> Tuple[str, str, Tuple, int]:
		return type(self).__name__, self.name, self.position, self.aperture
	def __repr__(self):
		return f'{type(self).__name__}: {self.name}'

class ReferenceStar(Star):
	def __init__(self, name : str, position : Tuple[int, int], aperture : int, magnitude : float):
		super().__init__(name, position, aperture)
		self.magnitude = magnitude
	@classmethod
	def From(cls, other : Star, magnitude : float = 0.0, **kwargs) -> Self:
		return cls(other.name, other.position, other.aperture, magnitude)
	def export(self):
		return (*super().export(), self.magnitude)

class TrackingMethod(Interface):
	@abstract
	def setup_model(self, *args):
		pass
	@abstract
	def track(self):
		pass