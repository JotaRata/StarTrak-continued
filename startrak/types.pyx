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
    cdef readonly dict[str, str] header
    cdef bint validated

    def FromHDU(hdu: fits.HDUList):
        if hdu is None: raise TypeError("No HDU list was given")
        if len(hdu) == 0: raise TypeError("Invalid HDU")
        ver = hdu.verify('fix')
        path = hdu.filename()
        sbytes = os.path.getsize(path)

        _header = hdu[0].header
        header = {key : _header[key] for key in _header}

        return FileInfo(path, sbytes, header, ver)