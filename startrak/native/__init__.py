from functools import lru_cache
import math
from typing import Any, Callable, ClassVar, Dict, Final, List, Optional, Set, Tuple, Type, cast, final
from abc import ABC, abstractmethod
import numpy as np
import os.path
from startrak.native.alias import ImageLike, NumberLike, ValueType, NDArray
from startrak.native.collections import Position, PositionArray, PositionLike
from startrak.native.fits import _FITSBufferedReaderWrapper as FITSReader
from startrak.native.fits import _bitsize
from mypy_extensions import mypyc_attr, trait

_defaults : Final[Dict[str, Type[ValueType]]] = \
		{'SIMPLE' : int, 'BITPIX' : int, 'NAXIS' : int, 'EXPTIME' : float, 'BSCALE' : float, 'BZERO' : float}

#region Structures
@mypyc_attr(allow_interpreted_subclasses=True)
@trait
class STObject:
	_sp : ClassVar[str] = '  '
	name : str
	def __iter__(self):
		for var in dir(self):
			if not var.startswith(('__', '_')) and var != 'name':
				attr = getattr(self, var)
				if callable(attr):
					continue
				yield var, attr
	def __pprint__(self, indent : int = 0) -> str:
		_ind = STObject._sp * (indent + 1)
		_str = ['', STObject._sp*indent + self.__class__.__name__ + ': ' + getattr(self, "name", "")]
		for key, value in self.__iter__():
			if isinstance(value, STObject):
				_str.append(_ind + f'{key}: {value.__pprint__(indent + 2)}')
			else:
				_str.append(_ind + f'{key}: {value}')
		return '\n'.join(_str)
	
	def __str__(self) -> str:
		return self.__pprint__()
	def __repr__(self) -> str:
		name = getattr(self, 'name', None)
		if name is None:
			return self.__class__.__name__
		return self.__class__.__name__ + ': ' + name
#endregion

#region File management
class Header(STObject):
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
	
	def __iter__(self):
		for key, val in self._items.items():
			yield key, val

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

class FileInfo(STObject):
	path : Final[str]
	size : Final[int]
	_file : FITSReader
	__header : Header | None

	def __init__(self, path : str):
		assert path.lower().endswith(('.fit', '.fits')),\
			'Input path is not a FITS file'
		self._file = FITSReader(path)
		self.path = os.path.abspath(path)
		self.name = os.path.basename(self.path)
		self.size = os.path.getsize(path)
		self.__header = None

	@property
	def header(self) -> Header:
		if self.__header is None:
			_dict = {key.rstrip() : value for key, value in self._file._read_header()}
			self.__header = Header(_dict)
			self.__header.name = self.name
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
	def __eq__(self, __value):
		if not  isinstance(__value, type(self)): return False
		return self.path == __value.path
	def __hash__(self) -> int:
		return hash(self.path)
#endregion

#region Sessions
@mypyc_attr(allow_interpreted_subclasses=True)
class Session(ABC, STObject):
	archetype : Optional[HeaderArchetype]
	included_items : Set[FileInfo]
	
	def __init__(self, name : str):
		self.name = name
		self.archetype : HeaderArchetype = None
		self.included_items : set[FileInfo] = set()

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
class PhotometryResult(STObject):
	flux : float
	flux_raw : float
	flux_iqr : float
	backg : float
	backg_sigma : float

	def __init__(self, *, flux : float, flux_raw : float,
					flux_range : float, background : float, background_sigma : float) -> None:
		self.flux = flux
		self.flux_raw = flux_raw
		self.flux_iqr = flux_range
		self.backg = background
		self.backg_sigma = background_sigma

	def __repr__(self) -> str:
		return str(self.flux)

@mypyc_attr(allow_interpreted_subclasses=True)
class Star(STObject):
	position : Position
	aperture : int
	photometry : Optional[PhotometryResult]

	def __init__(self, name : str, position : Position|PositionLike, 
					aperture : int = 16, photometry : Optional[PhotometryResult] = None) -> None:
		self.name = name
		self.position = Position.new(position)
		self.aperture = aperture
		self.photometry = photometry

	@property
	def flux(self) -> float:
		if not self.photometry:
			return 0
		return self.photometry.flux

class ReferenceStar(Star):
	magnitude : float = 0

@mypyc_attr(allow_interpreted_subclasses=True)
class PhotometryBase(ABC):
	@abstractmethod
	def evaluate(self, img : ImageLike, position : Position | PositionLike, aperture: int) -> PhotometryResult:
		pass

	def evaluate_star(self, img : ImageLike, star : Star) -> PhotometryResult:
		return self.evaluate(img, star.position, star.aperture)

#endregion
#region Tracking

class TrackingSolution(STObject):
	_dx : float
	_dy : float
	_da : float
	error : float
	lost : List[int]
	
	def __init__(self, *,delta_pos : PositionArray,
								delta_angle : NDArray[np.float_],
								image_size : Tuple[int, ...],
								weights : NDArray[np.float_]|None = None,
								lost_indices : List[int] = [],
								rejection_sigma : int = 3,
								rejection_iter = 1):
		assert len(delta_pos) > 1
		NAN = np.nan
		j, k = image_size[0]/2, image_size[1]/2

		mask = list(range(len(delta_pos)))
		pos_residuals = delta_pos - np.nanmean(delta_pos, axis= 0)
		ang_residuals = delta_angle - np.nanmean(delta_angle, axis= 0)
		for _ in range(rejection_iter):

			pos_std : float =  np.nanmean(np.power(pos_residuals[mask], 2))
			ang_std : float =  np.nanmean(np.power(ang_residuals[mask], 2))
			rej_count, rej_error = 0, 0.0
			exx: float; eyy: float; eaa : float
			for i, (exx, eyy) in enumerate(pos_residuals):
				isnan = math.isnan(exx + eyy)
				if ((err:= exx**2 + eyy**2) > max(rejection_sigma * pos_std, 1)) or isnan:
					if i in mask:
						mask.remove(i)
						lost_indices.append(i)
						if not isnan:
							rej_error += err; rej_count += 1
			for i, eaa in enumerate(ang_residuals):
				isnan = math.isnan(eaa)
				if (eaa**2 > max(rejection_sigma * ang_std, 1)) or isnan:
					if i in mask:
						mask.remove(i)
						lost_indices.append(i)
						if not isnan:
							rej_error += eaa * image_size[0]/2; rej_count += 1
			if rej_count > 0:
				print(f'{rej_count} stars deviated from the solution with average error: {np.sqrt(rej_error/rej_count):.2f}px (iter {_+1})')

		if weights is not None:
			weights = weights[mask]
			if np.sum(weights) == 0:
				weights = None
		
		self._dx, self._dy = np.average(delta_pos[mask], axis= 0, weights= weights).tolist()
		self._da = np.average(delta_angle[mask], weights= weights)

		ex, ey = np.nanstd(delta_pos[mask], axis= 0)
		self.error = (ex**2 + ey**2) ** 0.5
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
	
	def __iter__(self):
		yield from [(self._dx, self._dy), self.rotation, self.error, self.lost]
	
	def __pprint__(self, indent: int = 0) -> str:
		__ = STObject._sp* (indent + 1)
		return ( f'{STObject._sp* indent}{type(self).__name__}: '
					f'\n{__}translation: {self._dx:.1f} px, {self._dy:.1f} px'
					f'\n{__}rotation:    {self.rotation:.2f}°'
					f'\n{__}error:       {self.error:.3f} px')

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
	def _detect(self, image : ImageLike) -> Tuple[PositionArray, List[float]]:
		raise NotImplementedError()

	@final
	def detect(self, image : ImageLike) -> List[Star]:
		positions, apertures = self._detect(image)
		if len(positions) == 0:
			print('No stars were detected, try adjusting the parameters')
			return List[Star]()
		return [Star(self.star_name + str(i), positions[i], int(apertures[i])) 
					for i in range(len(positions))]
#endregion