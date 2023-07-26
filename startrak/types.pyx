import os
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from astropy.io import fits

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
class SessionBase(ABC):
    currentSession : SessionBase = None

    def __init__(self):
        raise TypeError(f'{type(self).__name__} cannot be directly instantiated'+
                        f'\nTry using {type(self).__name__}.Create()')

    def __repr__(self) -> str:
        return f'{type(self).__name__}: ' + str(", ".join(
            [f'{k} = {v}' for k, v in self.__dict__.items()]))
    
    def __post_init__(self):
        self.name = 'New Session'
        self.working_dir = ''
        self.file_arch = None
        self.creation_time = datetime.now()
        return self
    @abstractmethod
    def _create(self, name, *args, **kwargs) -> SessionBase: pass
    @abstractmethod 
    def save(self, out): pass

class InspectionSession(SessionBase):
    def _create(session, name : str, *args, **kwargs) -> SessionBase:
        session.name = name
        session.source_files = []
        return session

    def add_file(self, file : FileInfo | list[FileInfo]):
        if file is FileInfo:
            self.source_files.append(file)
        elif file is list:
            self.source_files += file
        else:
            raise ValueError(type(file))
    
    def save(self, out : str):
        pass    # todo: Add logic for saving sessions

class ScanSession(SessionBase):
    def _create(session, name, scan_dir, *args, **kwargs) -> SessionBase:
        session.name = name
        session.working_dir = scan_dir
        return session

    def save(self, out):
        pass
# -------------------------------------
