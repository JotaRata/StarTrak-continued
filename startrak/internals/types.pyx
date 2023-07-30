from operator import call
import os
from enum import Enum
from startrak.internals.exceptions import *
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, cast, Callable
from astropy.io import fits

# ---------------------- Headers -------------------------------
cdef class Header():
    cdef dict _items
    def __init__(self, source : fits.Header | dict):
        allowed_types = (int, bool, float, str)
        self._items = {str(key) : value for key, value in source.items() 
            if type(value) in allowed_types}
    
    def contains_key(self, key : str):
        return key in self._items.keys()
    def __getitem__(self, key : str):
        return self._items[key]
    def __getattr__(self, __name: str) -> Any:
        return self._items[__name]
    def __setattr__(self, __name: str, __value: Any) -> None:
        raise ImmutableError(self)
    def __repr__(self) -> str:
        return '\n'.join([f'{k} = {v}' for k,v in self._items.items()])

cdef class HeaderArchetype(Header):
    def __init__(self, source : Header | dict) -> None:
        _simple = source['SIMPLE'] == 1
        _bitpix = int(source['BITPIX'])
        _naxis = int(source['NAXIS'])
        _exptime = float(source['EXPTIME'])
        _naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(_naxis))
        
        self._items = {'SIMPLE':_simple, 'BITPIX':_bitpix,
                        'NAXIS':_naxis, 'EXPTIME':_exptime}
        for n in range(_naxis): self._items[f'NAXIS{n+1}'] = _naxisn[n]
    
    def validate(self, header : Header, failed : Callable[[str, Any, Any]] = None):
        for key, value in self._items.items():
            if (key not in header._items.keys()) or (header._items[key] != value):
                if callable(failed): failed(key, value, header._items[key])
                return False
        return True

# -------------- Files ----------------
@dataclass(frozen=True)
cdef class FileInfo():
    cdef readonly str path
    cdef readonly int size
    cdef readonly Header header

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
        
        header = Header(_header)
        return FileInfo(path, sbytes, header)

# ------------- Sessions --------------
class Session(ABC):
    currentSession : Session

    def __init__(self):
        raise InstantiationError(self, 'Session.Create')

    def __repr__(self) -> str:
        return f'{type(self).__name__}: ' + str(", ".join(
            [f'{k} = {v}' for k, v in self.__dict__.items()]))
    
    def __post_init__(self):
        self.name = 'New Session'
        self.working_dir : str = str()
        self.archetype : HeaderArchetype = None
        self.tracked_items : set[FileInfo] = set()
        self.creation_time = datetime.now()
        return self

    def add_item(self, item : Any | list): 
        _items = item if type(item) is list else [item]
        _added = {_item for _item in _items if type(_item) is FileInfo}
        if len(self.tracked_items) == 0:
            first = next(iter(_added))
            assert isinstance(first, FileInfo)
            self.set_archetype(first.header)
        
        self.tracked_items |= _added
        self.__item_added__(_added)
        # todo: raise warning if no items were added

    def remove_item(self, item : Any | list): 
        _items = item if type(item) is list else [item]
        _removed = {_item for _item in _items if type(_item) is FileInfo}
        self.tracked_items -= _removed
        self.__item_removed__(_removed)
    
    def set_archetype(self, header : Header):
        if header is None: self.archetype = None
        self.archetype = HeaderArchetype(header)
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
