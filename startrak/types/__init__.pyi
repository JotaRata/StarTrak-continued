# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\__init__.pyx"

import os.path
from astropy.io import fits as _astropy
import numpy

class Header():
	def __init__(self, source : _astropy.Header | dict): ...

class HeaderArchetype(Header):
	def __init__(self, source : Header | dict): ...
	def validate(self, header : Header, failed : callable = None): ...

class FileInfo():
	path : str
	size : int
	header : Header
	def from_path(path : str): ...
	def from_hdu(hduList : _astropy.HDUList): ...
	def get_data(self) -> numpy.ndarray: ...


class Star():
	name : str
	position : tuple[int, int]
	def __init__(self, name : str, position : tuple[int, int]): ...
