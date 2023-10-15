from functools import lru_cache
import math
from typing import Any, Callable, ClassVar, Dict, Final, Generic, Iterator, List, Optional, Self, Set, Tuple, Type, TypeVar, cast
from abc import ABC, abstractmethod
import numpy as np
from dataclasses import  dataclass
import os.path
from startrak.native.alias import ImageLike, NumberLike, PositionArray, ValueType, Position, NDArray
from startrak.native.fits import _FITSBufferedReaderWrapper as FITSReader
from startrak.native.fits import _bitsize
from mypy_extensions import mypyc_attr

_defaults : Final[Dict[str, Type[ValueType]]] = \
		{'SIMPLE' : int, 'BITPIX' : int, 'NAXIS' : int, 'EXPTIME' : float, 'BSCALE' : float, 'BZERO' : float}

#region File management
class Header():
	_items : Dict[str, ValueType]
	bitsize : np.dtype[NumberLike]
	shape : Tuple[int, int]
	bscale : np.uint
	bzero : np.uint
	def __init__(self, source : Dict[str, ValueType]):
		self._items = {str(key) : value for key, value in  source.items() 
			if type(value) in (int, bool, float, str)}
		if not all((key in self._items for key in _defaults.keys())):
			raise KeyError('Header not having mandatory keywords')
		self.bitsize = _bitsize(cast(int, self._items['BITPIX']))
		self.bscale = cast(np.uint,self._items['BSCALE'])
		self.bzero = cast(np.uint,self._items['BZERO'])
		
		# todo: Add support for ND Arrays
		if self._items['NAXIS'] != 2:
			raise NotImplementedError('Only 2D data blocks are supported')
		self.shape = cast(int, self._items['NAXIS2']),cast(int, self._items['NAXIS1'])
	def contains_key(self, key : str):
		return key in self._items.keys()
	def __getitem__(self, key : str):
		return self._items[key]
	def __getattr__(self, __name: str):
		return self._items[__name]
	def __repr__(self) -> str:
		return '\n'.join([f'{k} = {v}' for k,v in self._items.items()])

class HeaderArchetype(Header):
	_entries : ClassVar[Dict[str, Type[ValueType]]] = {}

	def __init__(self, source : Header | Dict[str, ValueType]):
		self._items = dict()
		for key, _type in _defaults.items():
			self._items[key] = _type(source[key])
		
		for key, _type in HeaderArchetype._entries.items():
			self._items[key] = _type(source[key])
		
		assert 'NAXIS' in self._items
		_naxis = self._items['NAXIS']
		assert type(_naxis) is int
		_naxisn = tuple(int(source[f'NAXIS{n + 1}']) for n in range(_naxis))
		for n in range(_naxis): self._items[f'NAXIS{n+1}'] = _naxisn[n]
	
	def validate(self, header : Header, failed : Optional[Callable[[str, ValueType, ValueType], None]] = None) -> bool:
		for key, value in self._items.items():
			if (key not in header._items.keys()) or (header._items[key] != value):
					if callable(failed): failed(key, value, header._items[key])
					return False
		return True

	@staticmethod
	def set_keywords(user_keys : Dict[str, type]):
		assert all([ type(key) is str  for key in user_keys])
		assert all([ value in (int, bool, float, str) for value in user_keys.values()])
		HeaderArchetype._entries = user_keys

@dataclass
class FileInfo():
	path : Final[str]
	size : Final[int]
	_file : FITSReader
	__header : Header | None

	def __init__(self, path : str):
		assert path.lower().endswith(('.fit', '.fits')),\
			'Input path is not a FITS file'
		self._file = FITSReader(path)
		self.path = os.path.abspath(path)
		self.size = os.path.getsize(path)
		self.__header = None

	@property
	def header(self) -> Header:
		if self.__header is None:
			_dict = {key.rstrip() : value for key, value in self._file._read_header()}
			self.__header = Header(_dict)
		return self.__header
	
	@lru_cache(maxsize=5)	# todo: Add parameter to config
	def get_data(self, scale = True) -> np.ndarray[Any, np.dtype[NumberLike]]:
		_dtype = self.header.bitsize
		_shape = self.header.shape
		_raw = self._file._read_data(_dtype.newbyteorder('>'), _shape[0] * _shape[1])
		if scale:
			_scale, _zero = self.header.bscale, self.header.bzero
			if _scale != 1 or _zero != 0:
				_raw = _zero + _scale * _raw
		return _raw.reshape(_shape).astype(_dtype)
	
	def __setattr__(self, __name: str, __value) -> None:
		raise AttributeError(name= __name)
	def __repr__(self):
		return f'\n{type(self).__name__}(path={os.path.basename(self.path)}, size={self.size} bytes)'
	def __eq__(self, __value):
		if not  isinstance(__value, type(self)): return False
		return self.path == __value.path
	def __hash__(self) -> int:
		return hash(self.path)
#endregion

#region Sessions
@mypyc_attr(allow_interpreted_subclasses=True)
class Session(ABC):
	name : str
	archetype : Optional[HeaderArchetype]
	included_items : Set[FileInfo]
	
	def __init__(self, name : str):
		self.name = name
		self.archetype : HeaderArchetype = None
		self.included_items : set[FileInfo] = set()
	
	def __repr__(self) -> str:
				return ( f'{type(self).__name__} : "{self.name}"\x7f\n'
							f'Included : {self.included_items}\n')

	def add_item(self, item : FileInfo | List[FileInfo]): 
		if type(item) is list:
			_items = item
		elif type(item) is FileInfo:
			_items = [item]
		else: raise TypeError()
		_added = {_item for _item in _items if type(_item) is FileInfo}
		if len(self.included_items) == 0:
			first = next(iter(_added))
			assert isinstance(first, FileInfo)
			self.set_archetype(first.header)
		
		self.included_items |= _added
		self.__item_added__(_added)
		# todo: raise warning if no items were added

	def remove_item(self, item : FileInfo | List[FileInfo]): 
		if type(item) is list:
			_items = item
		elif type(item) is FileInfo:
			_items = [item]
		else: raise TypeError()
		_removed = {_item for _item in _items if type(_item) is FileInfo}
		self.included_items -= _removed
		self.__item_removed__(_removed)
	
	def set_archetype(self, header : Optional[Header]):
		if header is None: 
			self.archetype = None
			return
		self.archetype = HeaderArchetype(header)

	@abstractmethod
	def __item_added__(self, added : Set[FileInfo]): pass
	@abstractmethod
	def __item_removed__(self, removed : Set[FileInfo]): pass
	@abstractmethod
	def save(self, out : str): pass

#endregion


#region Photometry
@mypyc_attr(allow_interpreted_subclasses=True)
@dataclass(frozen=True)
class PhotometryResult:
	flux : float
	flux_raw : float
	flux_iqr : float
	backg : float
	backg_sigma : float

@mypyc_attr(allow_interpreted_subclasses=True)
class Star:
	name : str
	position : Position
	aperture : int
	photometry : Optional[PhotometryResult]
	
	def __init__(self, name : str, position : Position, aperture : int) -> None:
		self.name = name
		self.position = position
		self.aperture = aperture
		self.photometry = None

	@property
	def flux(self) -> float:
		if not self.photometry:
			return 0
		return self.photometry.flux
	
	def __iter__(self):
		for var in dir(self):
			if not var.startswith(('__', '_')):
				yield var, getattr(self, var)

	def __repr__(self) -> str:
		s = [ f' {key}: {value}' for key, value in self.__iter__()]
		return self.__class__.__name__ + ':\n' + '\n'.join(s)

class ReferenceStar(Star):
	magnitude : float = 0

@mypyc_attr(allow_interpreted_subclasses=True)
class PhotometryBase(ABC):
	@abstractmethod
	def evaluate(self, img : ImageLike, position : Position, aperture: int) -> PhotometryResult:
		pass

	def evaluate_star(self, img : ImageLike, star : Star) -> PhotometryResult:
		return self.evaluate(img, star.position, star.aperture)

#endregion
#region Tracking

class TrackingSolution:
	dx : float
	dy : float
	da : float
	error : float
	lost : List[int]
	_center : Tuple
	
	# todo: optimize this mess
	def __init__(self, current : PositionArray, model : PositionArray, 
					img_shape : Tuple, lost_star_indices : List[int]) -> None:
		self.lost = lost_star_indices
		_diff = current - model
		errors = _diff - np.nanmean(_diff, axis= 0)

		for i, (exx, eyy) in enumerate(errors):
			if (_err:= exx**2 + eyy**2) > max(2 * np.nanmean(errors**2), 1):
				print(f'Star {i} is deviating from the solution ({_err:.1f} px)')
				self.lost.append(i)

		# self._center = img_shape[0] / 2, img_shape[1] / 2
		bad_mask = [index not in self.lost for index in range(len(model))]
		self._center = tuple(np.nanmean(current[bad_mask], axis=0).tolist())
		c_previous = model[bad_mask] - self._center
		c_current = current[bad_mask] - self._center

		_dot = np.nansum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		self.da = np.nanmean(np.arctan2(_cross,  _dot))

		ex, ey = np.nanstd(_diff[bad_mask], axis= 0)
		self.error = np.sqrt(ex**2 + ey**2)
		self.dx, self.dy = np.nanmean(_diff[bad_mask], axis= 0)

	@classmethod
	def identity(cls) -> Self:
		return cls.__new__(cls)
	@property
	def matrix(self) -> np.ndarray:
		c = math.cos(self.da)
		s = math.sin(self.da)

		j, k = self._center
		a = self.dx + j - j * c + k * s
		b = self.dy + k - k * c - j * s
		return np.array([ [c, -s, a], 
								[s,  c, b],
								[0,  0, 1]])
	@property
	def translation(self) -> np.ndarray:
		return np.array((self.dx, self.dy))
	
	@property
	def rotation(self) -> float:
		return np.degrees(self.da)
	
	def __repr__(self) -> str:
		return ( f'{type(self).__name__} ['
					f'\n  translation: {self.dx:.1f} px, {self.dy:.1f} px'
					f'\n  rotation:    {self.rotation:.2f}°'
					f'\n  error:       {self.error:.3f} px')
	def __setattr__(self, __name: str, __value) -> None:
		raise AttributeError(name= __name)

@mypyc_attr(allow_interpreted_subclasses=True)
class Tracker(ABC):
	@abstractmethod
	def setup_model(self, stars : List[Star]):
		pass
	@abstractmethod
	def track(self, image : ImageLike) -> TrackingSolution:
		pass

#endregion
