import os.path
from startrak.internals.types cimport Header
from astropy.io import fits as _astropy

cdef class FileInfo():
	cdef readonly str path
	cdef readonly int size
	cdef readonly Header header

	def __init__(self, hduList : _astropy.HDUList):
		if hduList is None: raise TypeError("No HDU list was given")
		if len(hduList) == 0: raise TypeError("Invalid HDU")
		path = hduList.filename()
		hdu = hduList[0]
		assert isinstance(path, str)
		assert isinstance(hdu, _astropy.PrimaryHDU)

		sbytes = os.path.getsize(path)
		_header = hdu.header
		
		header = Header(_header)
		return FileInfo(path, sbytes, header)

cdef class Star():
	cdef public str name
	cdef public int[2] position

	def __init__(self, str name, tuple position):
		self.name = name
		assert len(position) == 2
		self.position = position