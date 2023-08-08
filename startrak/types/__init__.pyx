import os.path
from .abstract cimport Interface
from .abstract import abstract
from astropy.io import fits as _astropy
from erfa import aper
from numpy cimport ndarray

cdef tuple __header_allowed_types = (int, bool, float, str)
cdef dict __archetype_entries = {'SIMPLE' : int, 'BITPIX' : int,
											'NAXIS' : int, 'EXPTIME' : float}
cdef dict __archetype_user_entries = dict()
cdef class Header():
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

cdef class HeaderArchetype(Header):
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
	
	def validate(self, Header header, failed : callable = None):
		for key, value in self._items.items():
			if (key not in header._items.keys()) or (header._items[key] != value):
					if callable(failed): failed(key, value, header._items[key])
					return False
		return True

	@staticmethod
	def set_keywords(dict user_keys):
		assert all([ type(key) is str  for key in user_keys])
		assert all([ value in __header_allowed_types for value in user_keys.values])
		global __archetype_user_entries
		__archetype_user_entries = user_keys

cdef class FileInfo():
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
	
	cpdef ndarray get_data(self):
		return _astropy.getdata(self.path)
	def __repr__(self):
		return f'\n[File: "{os.path.basename(self.path)}" ({self.size}) bytes]'

cdef class Star():
	def __init__(self, str name, tuple position, int aperture):
		self.name = name
		assert len(position) == 2
		self.position = position
		self.aperture = aperture
	@classmethod
	def From(cls, Star other):
		return cls(other.name, other.position, other.aperture)
	def export(self):
		return type(self).__name__, self.name, self.position, self.aperture
	def __repr__(self):
		return f'{type(self).__name__}: {self.name}'

cdef class ReferenceStar(Star):
	def __init__(self, str name, tuple position, int aperture, float magnitude):
		super().__init__(name, position, aperture)
		self.magnitude = magnitude
	@classmethod
	def From(cls, Star other, float magnitude):
		return cls(other.name, other.position, other.aperture, magnitude)
	def export(self):
		return (*super().export(), self.magnitude)

cdef class TrackingMethod(Interface):
	@abstract
	def setup_model(self, *args):
		pass
	@abstract
	def track(self):
		pass