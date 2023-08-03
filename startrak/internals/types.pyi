# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\internals\types.pyx"

import os
from startrak.internals.exceptions import *
from dataclasses import dataclass
from typing import Any, Callable
from astropy.io import fits
# ---------------------- Headers -------------------------------

class Header():
    def __init__(self, source : fits.Header | dict): ...

class HeaderArchetype(Header):
    def __init__(self, source : Header | dict) -> None: ...
    def validate(self, header : Header, failed : Callable[[str, Any, Any]] = None): ...
# -------------- Files ----------------

class FileInfo():
    def fromHDU(hduList: fits.HDUList | Any): ...
# ----------------- Data types --------------------

class Star():
    name : str
    position : int[2]
    def __init__(self, name : str, position : tuple[int]): ...
