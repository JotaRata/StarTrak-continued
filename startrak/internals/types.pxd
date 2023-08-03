cdef class Header():
	cdef dict _items

cdef class HeaderArchetype(Header):
	pass
# -------------- Files ----------------

cdef class FileInfo():
	cdef readonly str path
	cdef readonly int size
	cdef readonly Header header