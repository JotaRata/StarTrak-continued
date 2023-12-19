# compiled module
from dataclasses import dataclass
from functools import lru_cache
import math
from typing import Any, Callable, ClassVar, Dict, Final, Iterable, Iterator, List, Optional, Self, Tuple, Type, cast
import numpy as np
import os.path
from startrak.native.alias import NumberLike, ValueType, NDArray
from startrak.native.collections.position import Position, PositionArray, PositionLike

from startrak.native.fits import _FITSBufferedReaderWrapper as FITSReader
from startrak.native.fits import _bitsize
from mypy_extensions import mypyc_attr
from startrak.native.ext import AttrDict, STObject, spaces

#region File management
_defaults : Final[Dict[str, Type[ValueType]]] = \
		{'SIMPLE' : int, 'BITPIX' : int, 'NAXIS' : int, 'EXPTIME' : float, 'BSCALE' : float, 'BZERO' : float}
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
		return self._items.__iter__()

	def __export__(self) -> AttrDict:
		return self._items.copy()

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

@dataclass #! Hotfix for __setattr__ until a proper mypyc fix is implemented
class FileInfo(STObject):
	__path : str
	__size : int
	__file : FITSReader
	__header : Header | None

	def __init__(self, path : str):
		assert path.lower().endswith(('.fit', '.fits')),\
			'Input path is not a FITS file'
		# self.closed = False
		STObject.__set_locked__(self, __locked= False)
		self.__file = FITSReader(path)
		self.__path = os.path.abspath(path)
		self.name = os.path.basename(self.__path)
		self.__size = os.path.getsize(path)
		self.__header = None
		STObject.__set_locked__(self, __locked= True)
	
	@property
	def path(self) -> str:
		return self.__path
	@property
	def size(self) -> int:
		return self.__size
	
	@property
	def header(self) -> Header:
		STObject.__set_locked__(self, __locked= False)
		if self.__header is None:
			_dict = {key.rstrip() : value for key, value in self.__file._read_header()}
			self.__header = Header(_dict)
			self.__header.name = self.name
		retval = self.__header
		STObject.__set_locked__(self, __locked= True)
		return retval
	
	@lru_cache(maxsize=5)	# todo: Add parameter to config
	def get_data(self, scale = True) -> np.ndarray[Any, np.dtype[NumberLike]]:
		_dtype = self.header.bitsize
		_shape = self.header.shape
		_raw = self.__file._read_data(_dtype.newbyteorder('>'), _shape[0] * _shape[1])
		if scale:
			_scale, _zero = self.header.bscale, self.header.bzero
			if _scale != 1 or _zero != 0:
				_raw = _zero + _scale * _raw
		return _raw.reshape(_shape).astype(_dtype)
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		return cls(attributes['path'])
	
	def __eq__(self, __value):
		if not  isinstance(__value, type(self)): return False
		return self.__path == __value.__path
	def __hash__(self) -> int:
		return hash(self.__path)
	
	def __setattr__(self, __name: str, __value: Any) -> None:
		return super().__setattr__(__name, __value)

	def __repr__(self) -> str:
		return super().__repr__()
	def __str__(self) -> str:
		return super().__str__()
	
#endregion



#region Photometry
@dataclass #! Hotfix for __setattr__ until a proper mypyc fix is implemented
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
	def __setattr__(self, __name: str, __value) -> None:
			raise AttributeError(name= __name)
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		params = {'flux':'flux', 'flux_raw':'flux_raw', 'flux_iqr':'flux_range', 'backg':'background', 'backg_sigma':'background_sigma'}

		attributes = {params[k]: attributes[k] for k in params if k in attributes}
		return cls(**attributes)
	
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
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		params = ('name', 'position', 'aperture', 'photometry')
		attributes = {k: attributes[k] for k in params if k in attributes}
		return cls(**attributes)

class ReferenceStar(Star):
	magnitude : float = 0

#endregion
#region Tracking
@dataclass #! Hotfix for __setattr__ until a proper mypyc fix is implemented
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
			if len(mask) == 0:
				break
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
		if len(mask) > 0:
			self._dx, self._dy = np.average(delta_pos[mask], axis= 0, weights= weights).tolist()
			self._da = np.average(delta_angle[mask], weights= weights)

			ex, ey = np.nanstd(delta_pos[mask], axis= 0)
			self.error = (ex**2 + ey**2) ** 0.5
			self.lost = lost_indices
		# If all values were masked out, then return the identity
		else:
			self._dx, self._dy = 0.0, 0.0
			self._da = 0.0
			self.error = 0.0
			self.lost = list(range(len(delta_pos)))

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
	
	def __export__(self) -> AttrDict:
		return {	'translation':(self._dx, self._dy), 
					"rotation": self._da, 
					"error": self.error, 
					"lost_indices": self.lost} 
	
	def __pprint__(self, indent: int = 0, compact : bool = False) -> str:
		if compact:
			return f'{type(self).__name__} ({self._dx:.1f} px, {self._dy:.1f} px, {self.rotation:.1f}°)'
		indentation = spaces * (indent + 1)
		return ( f'{spaces * indent}{type(self).__name__}: '
					'\n' + indentation + f'translation: {self._dx:.1f} px, {self._dy:.1f} px'
					'\n' + indentation + f'rotation:    {self.rotation:.2f}°'
					'\n' + indentation + f'error:       {self.error:.3f} px')

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



#endregion

