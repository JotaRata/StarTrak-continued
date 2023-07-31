# Auto generated stub
# file: "c:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\internals\types.pyx"

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

class Header():
    def __init__(self, source : fits.Header | dict): ...

class HeaderArchetype(Header):
    def __init__(self, source : Header | dict) -> None: ...
    def validate(self, header : Header, failed : Callable[[str, Any, Any]] = None): ...
# -------------- Files ----------------

class FileInfo():
    path : str
    size : int
    header : Header
    def fromHDU(hduList: fits.HDUList | Any): ...
# ------------- Sessions --------------

class Session(ABC):
    name = 'New Session'
    working_dir : str 
    archetype : HeaderArchetype 
    tracked_items : set[FileInfo]
    creation_time = datetime.now()
    def __init__(self): ...
        # todo: raise warning if no items were added
    def save(self, out): ...

class InspectionSession(Session):
    def save(self, out : str): ...

class ScanSession(Session):
    def save(self, out): ...
# -------------------------------------
