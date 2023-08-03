import os

from startrak.internals.exceptions import *
from dataclasses import dataclass
from typing import Any, Callable
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
