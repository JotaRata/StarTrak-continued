import os.path
from astropy.io import fits as _astropy
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

# This prevents the user for creating invalid FileInfo objects
cdef object __startrak_factory_obj = object()
cdef class FileInfo():
	def __init__(self, str path, int size, Header header, *args):
		assert len(args) == 1 and args[0] == __startrak_factory_obj, \
			'FileInfo must only be created using one of the two factory methods\n FileInfo.from_path(str) and FileInfo.from_hdu(HDU-like).'
		self.path = path
		self.size = size
		self.header = header
	@staticmethod
	def from_path(str path):
		hdu = _astropy.open(path)
		size = os.path.getsize(path)
		assert isinstance(hdu[0], _astropy.PrimaryHDU)
		header = Header(hdu[0].header)
		path = os.path.abspath(path)
		hdu.close()
		return FileInfo(path, size, header, __startrak_factory_obj)
	@staticmethod
	def from_hdu(hdu):
		if hdu is None: raise TypeError("No HDU list was given")
		assert isinstance(hdu, _astropy.HDUList)
		path = os.path.abspath(hdu.filename())
		size = os.path.getsize(path)
		phdu = hdu[0]
		header = Header(phdu.header)
		return FileInfo(path, size, header, __startrak_factory_obj)
	
	cpdef ndarray get_data(self):
		return _astropy.getdata(self.path)
	def __repr__(self):
		return f'\n[File: "{os.path.basename(self.path)}" ({self.size}) bytes]'

cdef class Star():
	def __init__(self, str name, tuple position):
		self.name = name
		assert len(position) == 2
		self.position = position