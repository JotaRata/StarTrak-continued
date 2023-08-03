# Auto generated Cython definitions
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\__init__.pyx"

import os.path
from astropy.io import fits as _astropy

cdef class Header():
	cdef dict _items
cdef class HeaderArchetype(Header): pass
cdef class FileInfo():
	cdef readonly str path
	cdef readonly int size
	cdef readonly Header header
cdef class Star():
	cdef public str name
	cdef public int[2] position
