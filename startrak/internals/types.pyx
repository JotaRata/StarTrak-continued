from operator import pos
cimport numpy as np
import os
from enum import Enum

from startrak.exceptions import *
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, cast, Callable
from astropy.io import fits

# ---------------------- Headers -------------------------------
cdef class Header():
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

# class InspectionSession(Session):
#     def _create(session, name : str, *args, **kwargs) -> Session:
#         session.name = name
#         return session

#     def __item_added__(self, added): pass
#     def __item_removed__(self, removed): pass

#     def save(self, out : str):
#         pass    # todo: Add logic for saving sessions

# class ScanSession(Session):
#     def _create(session, name, scan_dir, *args, **kwargs) -> Session:
#         session.name = name
#         session.working_dir = scan_dir
#         return session

#     def __item_added__(self, added): pass
#     def __item_removed__(self, removed): pass

#     def save(self, out):
#         pass

# ----------------- Data types --------------------

cdef class Star():
    cdef public str name
    cdef public int[2] position

    def __init__(self, str name, tuple position):
        self.name = name
        assert len(position) == 2
        self.position = position