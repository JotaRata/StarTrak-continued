# Auto generated Cython definitions
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\__init__.pyx"

import os.path
from typing import Any
from astropy.io import fits as _astropy
from numpy cimport ndarray

cdef class Header():
	cdef dict _items
cdef class HeaderArchetype(Header): pass
cdef class FileInfo():
	cdef readonly str path
	cdef readonly int size
	cdef readonly Header header
	
	cpdef ndarray get_data(self : Any)

cdef class Star():
	cdef public str name
	cdef public int[2] position
	cdef public int aperture
cdef class ReferenceStar(Star):
	cdef public float magnitude
