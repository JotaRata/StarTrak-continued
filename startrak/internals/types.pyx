import os
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, cast
from astropy.io import fits

@dataclass(frozen=True)
cdef class FileInfo():
    cdef readonly str path
    cdef readonly int size
    cdef readonly dict[str, str] header

    @staticmethod
    def fromHDU(hduList: fits.HDUList | Any):
        if hduList is None: raise TypeError("No HDU list was given")
        if len(hduList) == 0: raise TypeError("Invalid HDU")
        path = hduList.filename()
        hdu = hduList[0]
        assert isinstance(path, str)
        assert isinstance(hdu, fits.PrimaryHDU)

        sbytes = os.path.getsize(path)
        _header = hdu.header

        header = {cast(str, key) : cast(str, _header[key]) for key in _header}
        return FileInfo(path, sbytes, header)

ctypedef fused HeaderType:
    int
    float
    bint
    str

cdef class Header():
    cdef dict[str, HeaderType] items
    def __init__(self, source : fits.Header | dict):
        self.items = {cast(str, key) : source[key] for key in source}
    def __getattr__(self, __name: str) -> Any:
        return self.items[__name]
    def __setattr__(self, __name: str, __value: Any) -> None:
        raise ValueError('Header class is immutable')
    def __repr__(self) -> str:
        return '\n'.join([f'{k} = {v}' for k,v in self.items.items()])

cdef class FileArchetype(Header):
    def __init__(self, source : fits.Header | dict) -> None:
        _simple = source['SIMPLE'] == 1
        _bitpix = int(source['BITPIX'])
        _naxis = int(source['NAXIS'])
        _exptime = float(source['EXPTIME'])
        _naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(self.NAXIS))
        
        self.items = {'SIMPLE':_simple, 'BITPIX':_bitpix,
                        'NAXIS':_naxis, 'EXPTIME':_exptime}
        for n in range(_naxis): self.items[f'NAXIS{n+1}'] = _naxisn[n]


# ------------- Sessions --------------
class Session(ABC):
    currentSession : Session

    def __init__(self):
        raise TypeError(f'{type(self).__name__} cannot be directly instantiated'+
                        f'\nTry using {type(self).__name__}.Create()')

    def __repr__(self) -> str:
        return f'{type(self).__name__}: ' + str(", ".join(
            [f'{k} = {v}' for k, v in self.__dict__.items()]))
    
    def __post_init__(self):
        self.name = 'New Session'
        self.working_dir : str
        self.file_arch : FileArchetype
        self.tracked_items : set[FileInfo]
        self.creation_time = datetime.now()
        return self

    def add_item(self, item : Any | list): 
        _items = item if type(item) is list else [item]
        _added = {_item for _item in _items if type(_item) is FileInfo}
        self.tracked_items |= _added
        self.__item_added__(_added)
        # todo: raise warning if no items were added

    def remove_item(self, item : Any | list): 
        _items = item if type(item) is list else [item]
        _removed = {_item for _item in _items if type(_item) is FileInfo}
        self.tracked_items -= _removed
        self.__item_removed__(_removed)
    
    @abstractmethod
    def _create(self, name, *args, **kwargs) -> Session: pass
    @abstractmethod
    def __item_added__(self, added): pass
    @abstractmethod
    def __item_removed__(self, removed): pass
    @abstractmethod 
    def save(self, out): pass

class InspectionSession(Session):
    def _create(session, name : str, *args, **kwargs) -> Session:
        session.name = name
        return session

    def __item_added__(self, added): pass
    def __item_removed__(self, removed): pass

    def save(self, out : str):
        pass    # todo: Add logic for saving sessions

class ScanSession(Session):
    def _create(session, name, scan_dir, *args, **kwargs) -> Session:
        session.name = name
        session.working_dir = scan_dir
        return session

    def __item_added__(self, added): pass
    def __item_removed__(self, removed): pass

    def save(self, out):
        pass
# -------------------------------------
