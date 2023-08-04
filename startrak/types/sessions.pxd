# Auto generated Cython definitions
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\sessions.pyx"

from startrak.types cimport FileInfo, HeaderArchetype, Header
from startrak.types.abstract cimport Interface
from startrak.types.abstract import abstract
from enum import StrEnum
cdef class Session(Interface):
	cdef public str name
	cdef public str working_dir
	cdef readonly HeaderArchetype archetype
	cdef readonly set[FileInfo] included_items
