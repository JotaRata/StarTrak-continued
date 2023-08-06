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
	def set_keywords(user_keys : dict[str, type]): ...
class FileInfo():
	path : str
	size : int
	header : Header
	def __init__(self, path_or_hdulist : str | _astropy.HDUList): ...
	def get_data(self) -> numpy.ndarray: ...


class Star():
	name : str
	position : tuple[int, int]
	aperture : int
	def __init__(self, name : str, position : tuple[int, int], aperture:int): ...
	@classmethod
	def From(cls, other : Star) -> Star: ...
class TrackingStar(Star):
	pass
class ReferenceStar(Star):
	magnitude : float
	def __init__(self, *star_args, magnitude : float): ...