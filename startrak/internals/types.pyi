# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\internals\types.pyx"

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

class Header():
    def __init__(self, source : fits.Header | dict): ...
    def contains_key(self, key : str): ...

class HeaderArchetype(Header):
    def __init__(self, source : Header | dict) -> None: ...
    def validate(self, header : Header, failed : Callable[[str, Any, Any]] = None): ...
# -------------- Files ----------------

class FileInfo():
    def fromHDU(hduList: fits.HDUList | Any): ...
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

class Star():
    name : str
    position : int[2]
    def __init__(self, str name, tuple position): ...
