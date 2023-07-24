import os
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod, abstractstaticmethod
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

    @staticmethod
    def fromHDU(hdu: fits.HDUList):
        if hdu is None: raise TypeError("No HDU list was given")
        if len(hdu) == 0: raise TypeError("Invalid HDU")
        ver = hdu.verify('fix')
        path = hdu.filename()
        sbytes = os.path.getsize(path)

        _header = hdu[0].header
        header = {key : _header[key] for key in _header}

        return FileInfo(path, sbytes, header, ver)

# ------------- Sessions --------------
@dataclass
class SessionBase(ABC):
    sessionName : str
    sessionType : SessionType
    workingDirectory : str = None
    sessionTime : datetime = datetime.now()
    fileArchetype : dict[str, str] = None

    @abstractstaticmethod
    def create(name, *args, **kwargs) -> SessionBase: pass
    @abstractmethod 
    def save(self, out): pass

@dataclass
class InspectionSession(SessionBase):
    source_files  : list[FileInfo] = None
    # Add stars, trackers, settings
    def create(name : str, source_files : list[FileInfo],*args, **kwargs) -> SessionBase:
        time =  datetime.utcnow()
        return InspectionSession(name, SessionType.ASTRO_INSPECT)
    def save(self, out : str):
        pass    # todo: Add logic for saving sessions
@dataclass
class ScanSession(SessionBase):
    def create(name, scan_dir, *args, **kwargs) -> SessionBase:
        time =  datetime.utcnow()
        return ScanSession(name, SessionType.ASTRO_SCAN, scan_dir)
    def save(self, out):
        pass
# -------------------------------------
