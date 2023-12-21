# compiled module
from __future__ import annotations
from mypy_extensions import mypyc_attr, i16, u8
from dataclasses import dataclass
from functools import lru_cache
import math
from typing import Any, Callable, ClassVar, Dict, Final, List, Optional, Self, Tuple, Type, cast
import numpy as np
import os.path
from startrak.native.alias import NumberLike, ValueType, NDArray
from startrak.native.collections.position import Position, PositionArray, PositionLike

from startrak.native.fits import _FITSBufferedReaderWrapper as FITSReader
from startrak.native.fits import _bitsize
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
	__private__ :  ClassVar[Tuple[str, ...] | None]  = ('all',)

	def __init__(
		self, *,
		flux: float,
		flux_raw: float,
		flux_sigma: float,
		flux_max: float,
		background: float,
		background_sigma: float,
		method: str,
		aperture_radius: Optional[float] = None,
		annulus_width: Optional[float] = None,
		annulus_offset: Optional[float] = None,
		psf_parameters: Optional[Tuple[float, float, float]] = None,
	):
		self.flux = flux
		self.flux_raw = flux_raw
		self.flux_sigma = flux_sigma
		self.flux_max = flux_max
		self.background = background
		self.background_sigma = background_sigma
		self.method = method
		self.aperture_radius = aperture_radius
		self.annulus_width = annulus_width
		self.annulus_offset = annulus_offset
		self.psf_parameters = psf_parameters
		STObject.__set_locked__(self, __locked= True)
	
	@property
	def snr(self) -> float:
		return self.flux / self.background
	@property
	def error(self) -> float:
		return math.sqrt(self.flux_sigma**2 + self.background_sigma**2)

	def __repr__(self) -> str:
		return str(self.flux)
	
	def __setattr__(self, __name: str, __value: Any) -> None:
		return super().__setattr__(__name, __value)
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		params = ('flux', 'flux_raw', 'flux_sigma',
					'flux_max', 'background',
					'background_sigma', 'method',
					'aperture_radius', 'annulus_width',
					'annulus_offset', 'psf_parameters')
		attributes = {k: attributes[k] for k in params if k in attributes}
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
	# Transform matrix is defined as
	# | a -b  c |
	# | b -a  d |
	# | 0  0  1 |
	_a : float							# a value of the transform matrix (cos(angle))
	_b : float							# b value of the transform matrix (sin(angle))
	_c : float							# c value of the transform matrix (dx)
	_d : float							# d value of the transform matrix (dy)
	_r : float							# rotation angle in radians
	
	def __init__(self, a : float, b : float,  c : float, d : float, e : 
									float, r : Optional[float] = None,  l : Optional[List[u8]] = None):
		self._a = a
		self._b = b
		self._c = c
		self._d = d
		self._err = e
		if l:
			self._lost = l
		if r:
			self._r = r
		else:
			self._r = math.atan2(a, b)

	def new(self, *,delta_pos : PositionArray,
								delta_angle : NDArray[np.float_],
								image_size : Tuple[int, ...],
								weights : Tuple[float, ...] | None = None,
								lost_indices : List[u8] = [],
								rejection_sigma : int = 3,
								rejection_iter : u8 = 1) -> TrackingSolution:

		mask = list(range(len(delta_pos)))
		pos_residuals = delta_pos - np.nanmean(delta_pos, axis= 0)
		ang_residuals = delta_angle - np.nanmean(delta_angle, axis= 0)
		
		for _ in range(rejection_iter):
			if len(mask) == 0:
				break
			pos_std : float =  np.nanmean(np.power(pos_residuals[mask], 2))
			ang_std : float =  np.nanmean(np.power(ang_residuals[mask], 2))
			rej_count, rej_error = 0, 0.0
			exx: float; eyy: float; eaa : float; i: u8
			# Translation error
			for i, (exx, eyy) in enumerate(pos_residuals):
				isnan = math.isnan(exx + eyy)
				if ((err:= exx**2 + eyy**2) > max(rejection_sigma * pos_std, 1)) or isnan:
					if i in mask:
						mask.remove(i)
						lost_indices.append(i)
						if not isnan:
							rej_error += err; rej_count += 1
			# Rotation Error
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
		
		# Initilize the matrix as the identity
		dx, dy = 0.0, 0.0
		r = 0.0
		e = 0.0
		l = list(range(len(delta_pos)))

		if len(mask) > 0:
			if weights is not None:
				weights = tuple(weights[i] for i in mask)
				sum_w = sum(weights)
				
				if sum_w > 0:
					dx = sum([pos.x * w for pos, w in zip(delta_pos[mask], weights)]) / sum_w
					dy = sum([pos.y * w for pos, w in zip(delta_pos[mask], weights)]) / sum_w
					r = sum([ang * w for ang, w in zip(delta_angle[mask], weights)]) / sum_w
				else:
					dx = sum([pos.x * w for pos, w in zip(delta_pos[mask], weights)]) / len(mask)
					dy = sum([pos.y * w for pos, w in zip(delta_pos[mask], weights)]) / len(mask)
					r = sum([ang * w for ang, w in zip(delta_angle[mask], weights)]) / len(mask)
			
			ex, ey = np.nanstd(delta_pos[mask], axis= 0)
			e = (ex**2 + ey**2) ** 0.5
			l = lost_indices

		j, k = image_size[0]/2, image_size[1]/2
		a = math.cos(r)
		b = math.sin(r)
		
		c = dx + j - j * a + k * b
		d = dy + k - k * a - j * b

		return TrackingSolution(a, b, c, d, e, r, l)

	@property
	def matrix(self) -> NDArray[np.float_]:
		return np.array([ [self._a, -self._b, self._c], 
								[self._b,  self._a, self._d],
								[0,           0,          1]])
	@property
	def translation(self) ->Position:
		return Position(self._c, self._d)
	
	@property	
	def rotation(self) -> float:
		return math.degrees(self._r)
	
	def __export__(self) -> AttrDict:
		return { 'rot' : self._r,
					'error' : self._err,
					'param_0' : self._a,
					'param_1' : self._b,
					'param_2' : self._c,
					'param_3' : self._d,
					'indices' : self._lost} 
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		params = {'rot' : 'r',
					'error' : 'e',
					'param_0' : 'a',
					'param_1' : 'b',
					'param_2' : 'c',
					'param_3' : 'd',
					'indices' : 'l'}
		kwargs = {params[k]: attributes[k] for k in params}
		return cls(**kwargs)
	
	def __pprint__(self, indent: int = 0, compact : bool = False) -> str:
		if compact:
			return f'{type(self).__name__} ({self._c:.1f} px, {self._d:.1f} px, {self.rotation:.1f}°)'
		indentation = spaces * (indent + 1)
		return ( f'{spaces * indent}{type(self).__name__}: '
					'\n' + indentation + f'translation: {self._c:.1f} px, {self._d:.1f} px'
					'\n' + indentation + f'rotation:    {self.rotation:.2f}°'
					'\n' + indentation + f'error:       {self._err:.3f} px')

	def __setattr__(self, __name: str, __value: Any) -> None:
		return super().__setattr__(__name, __value)

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

