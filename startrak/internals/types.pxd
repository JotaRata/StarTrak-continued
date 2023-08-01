cdef class Header():
    cdef dict _items

cdef class HeaderArchetype(Header):
    pass
# -------------- Files ----------------

cdef class FileInfo():
    cdef str path
    cdef int size
    cdef Header header