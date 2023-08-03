# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\__init__.pyx"

import os.path
from startrak.internals.types import Header
from astropy.io import fits as _astropy

class FileInfo():
	path : str
	size : int
	header : Header
	def __init__(self, hduList : _astropy.HDUList): ...

class Star():
	name : str
	position : int[2]
	def __init__(self, str name, tuple position): ...
