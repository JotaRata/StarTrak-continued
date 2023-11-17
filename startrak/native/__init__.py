from functools import lru_cache
import math
from typing import Any, Callable, ClassVar, Dict, Final, Generic, Iterator, List, Optional, Self, Set, Tuple, Type, TypeVar, cast, final, get_args
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

class TrackingSolution():
	_dx : float
	_dy : float
	_da : float
	error : float
	lost : List[int]
	
	def __init__(self, *,delta_pos : NDArray[np.float_],
								delta_angle : NDArray[np.float_],
								image_size : Tuple[int, ...],
								lost_indices : List[int] = [],
								error_sigma : int = 3,
								error_iter = 1):
		assert len(delta_pos) > 1
		if image_size == (0, 0): return	# Identity  code
		j, k = image_size[0]/2, image_size[1]/2

		mask = list(range(len(delta_pos)))
		pos_residuals = delta_pos - np.nanmean(delta_pos, axis= 0)
		ang_residuals = delta_angle - np.nanmean(delta_angle, axis= 0)
		for _ in range(error_iter):
			rej_count, rej_error = 0, 0.0
			for i, (exx, eyy) in enumerate(pos_residuals):
				if (err:= exx**2 + eyy**2) > max(error_sigma * np.nanmean(pos_residuals[mask]**2), 1):
					if i in mask:
						mask.remove(i)
						lost_indices.append(i)
						rej_error += err; rej_count += 1
			for i, eaa in enumerate(ang_residuals):
				if eaa**2 > max(error_sigma * np.nanmean(ang_residuals[mask]**2), 1):
					if i in mask:
						mask.remove(i)
						lost_indices.append(i)
						rej_error += eaa * image_size[0]/2; rej_count += 1
			if rej_count > 0:
				print(f'{rej_count} stars deviated from the solution with average error: {np.sqrt(rej_error/rej_count):.2f}px (iter {_+1})')

		self._dx, self._dy = np.nanmean(delta_pos[mask], axis= 0).tolist()
		self._da = np.nanmean(delta_angle[mask])

		ex, ey = np.nanstd(delta_pos[mask], axis= 0)
		self.error = np.sqrt(ex**2 + ey**2)
		self.lost = lost_indices

		c = math.cos(self._da)
		s = math.sin(self._da)
		a = self._dx + j - j * c + k * s
		b = self._dy + k - k * c - j * s
		self._matrix = np.array([ [c, -s, a], 
											[s,  c, b],
											[0,  0, 1]])

	@property
	def matrix(self) -> np.ndarray:
		return self._matrix
	@property
	def translation(self) -> np.ndarray:
		return np.array((self._dx, self._dy))
	
	@property	
	def rotation(self) -> float:
		return np.degrees(self._da)
	
	def __repr__(self) -> str:
		return ( f'{type(self).__name__}: '
					f'\n  translation: {self._dx:.1f} px, {self._dy:.1f} px'
					f'\n  rotation:    {self.rotation:.2f}°'
					f'\n  error:       {self.error:.3f} px')
	def __setattr__(self, __name: str, __value) -> None:
		raise AttributeError(name= __name)

class TrackingIdentity(TrackingSolution):
	def __init__(self):
		self._dx, self._dy = 0., 0.
		self._da = 0.
		self.error = 0.
		self.lost = []
		self._matrix =np.array([[1, 0, 0], 
										[0, 1, 0],
										[0, 0, 1]])

@mypyc_attr(allow_interpreted_subclasses=True)
class Tracker(ABC):
	@abstractmethod
	def setup_model(self, stars : List[Star]):
		pass
	@abstractmethod
	def track(self, image : ImageLike) -> TrackingSolution:
		pass

#endregion

#region Detectors
@mypyc_attr(allow_interpreted_subclasses=True)
class StarDetector(ABC):
	star_name : str = 'star_'
	@abstractmethod
	def _detect(self, image : ImageLike) -> List[List[float]]:
		raise NotImplementedError()

	@final
	def detect(self, image : ImageLike) -> List[Star]:
		result = self._detect(image)
		if len(result) == 0:
			print('No stars were detected, try adjusting the parameters')
			return list[Star]()
		return [Star(self.star_name + str(i), ( int(x), int(y) ), int(rad)) 
					for i, (x, y, rad) in enumerate(result)]
#endregion