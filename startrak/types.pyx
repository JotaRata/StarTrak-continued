import os
from enum import Enum
from dataclasses import dataclass
from astropy.io import fits

class SessionType(Enum):
    ASTRO_SCAN = 1
    ASTRO_INSPECT = 2


@dataclass(frozen=True)
cdef class FileInfo():
    cdef readonly str path
    cdef readonly int size
    cdef readonly list headers
    cdef bint validated

    def FromHDU(hdu_list: fits.HDUList):
        if hdu_list is None: raise TypeError("No HDU list was given")
        path = hdu_list.filename()
        sbytes = os.path.getsize(path)
        ver = hdu_list.verify('fix')
        headers = [hdu.header for hdu in hdu_list]

        return FileInfo(path, sbytes, ver, headers)
