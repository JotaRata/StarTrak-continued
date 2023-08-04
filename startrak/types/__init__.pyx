import os.path
from astropy.io import fits as _astropy


cdef class Header():
	def __init__(self, source : _astropy.Header | dict):
		allowed_types = (int, bool, float, str)
		self._items = {str(key) : value for key, value in source.items() 
			if type(value) in allowed_types}
	
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
		_simple = source['SIMPLE'] == 1
		_bitpix = int(source['BITPIX'])
		_naxis = int(source['NAXIS'])
		_exptime = float(source['EXPTIME'])
		_naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(_naxis))
		
		self._items = {'SIMPLE':_simple, 'BITPIX':_bitpix,
							'NAXIS':_naxis, 'EXPTIME':_exptime}
		for n in range(_naxis): self._items[f'NAXIS{n+1}'] = _naxisn[n]
	
	def validate(self, Header header, failed : callable = None):
		for key, value in self._items.items():
			if (key not in header._items.keys()) or (header._items[key] != value):
					if callable(failed): failed(key, value, header._items[key])
					return False
		return True

cdef class FileInfo():
	def __init__(self, hduList : _astropy.HDUList):
		if hduList is None: raise TypeError("No HDU list was given")
		if len(hduList) == 0: raise TypeError("Invalid HDU")
		self.path = hduList.filename()
		hdu = hduList[0]
		assert isinstance(self.path, str)
		assert isinstance(hdu, _astropy.PrimaryHDU)

		self.size = os.path.getsize(self.path)
		_header = hdu.header
		self.header = Header(_header)
	
	def __repr__(self):
		return f'[File: {self.path} ({self.size}) bytes]\n'

cdef class Star():
	def __init__(self, str name, tuple position):
		self.name = name
		assert len(position) == 2
		self.position = position