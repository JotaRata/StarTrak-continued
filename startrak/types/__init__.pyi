# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\__init__.pyx"

import os.path
from astropy.io import fits as _astropy

class Header():
	def __init__(self, source : _astropy.Header | dict): ...

class HeaderArchetype(Header):
	def __init__(self, source : Header | dict): ...
	def validate(self, header : Header, failed : callable): ...

class FileInfo():
	def __init__(self, hduList : _astropy.HDUList): ...

class Star():
	def __init__(self, name : str, position : tuple[int, int]): ...
