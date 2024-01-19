# compiled module
from __future__ import annotations
from mypy_extensions import mypyc_attr
import math
from typing import Any, Callable, ClassVar, Dict, Final, List, NamedTuple, Optional, Self, Tuple, Type, TypeVar, Union, cast, overload
import numpy as np
import os.path
from startrak.native.alias import RealDType, ValueType, ArrayLike
from startrak.native.collections.native_array import Array
from startrak.native.collections.position import Position, PositionArray, PositionLike

from startrak.native.fits import _bound_reader, _get_header
from startrak.native.ext import AttrDict, STObject, _register_class, spaces
from startrak.native.matrices import Matrix2x2, Matrix3x3
from startrak.native.numeric import average
from startrak.native.utils.svdutils import SVD, outer

_min_required : Final[Dict[str, Tuple[type, ...]]] = \
		{'SIMPLE' : (bool,), 'BITPIX' : (int,), 'NAXIS' : (int,)}

_EXPORT_PATH : str | None = None	# Canot use early bindign since its dynamic

class RelativeContext:
	def __init__(self, new_dir : str) -> None:
		self.new_dir = new_dir
	@staticmethod
	def set(new_dir : str):
		global _EXPORT_PATH
		_EXPORT_PATH = new_dir
	@staticmethod
	def reset():
		global _EXPORT_PATH
		_EXPORT_PATH = None
	def __enter__(self) -> Self:
		RelativeContext.set(self.new_dir)
		return self
	def __exit__(self, *args):
		RelativeContext.reset()

# todo: Add support for ND Arrays
TValue = TypeVar('TValue', bound= Union[ValueType, RealDType])
class Header(STObject):
	linked_file : str
	__dict__ : dict[str, ValueType]

	def __init__(self, linked_filepath : str, source : Dict[str, ValueType]):
		assert all( [key in source and isinstance(source[key], cls)  for key, cls in _min_required.items()]), "FITS Header doesn't have the minimum required keywords"
		assert source['NAXIS'] == 2, 'Only 2D data blocks are supported'
		self.__dict__ = source
		self.linked_file = linked_filepath
		self.name = os.path.basename(linked_filepath)

	
	@property
	def shape(self) -> Tuple[int, int]:
		return cast(int, self['NAXIS2']),cast(int, self['NAXIS1'])
	
	def items(self):
		return self.__dict__.items()
	def keys(self):
		return self.__dict__.keys()
	def values(self):
		return self.__dict__.values()
	def copy(self):
		return Header( self.__dict__.copy())
	@overload
	def __getitem__(self, __key: Tuple[str, Type[TValue], TValue]) -> TValue: ...
	@overload
	def __getitem__(self, __key: Tuple[str, Type[TValue]]) -> TValue: ...
	@overload
	def __getitem__(self, __key: str) -> ValueType: ...
	def __getitem__(self, key: str | Tuple[str, Type[TValue]] | Tuple[str, Type[TValue], TValue]) -> ValueType | RealDType:
		if isinstance(key, tuple):
			if len(key) == 2:
				key, cls = cast(Tuple[str, Type[TValue]] , key)
				return cls(self.__dict__.__getitem__(key))
			elif len(key) == 3:
				key, cls, _def = cast(Tuple[str, Type[TValue], TValue], key)
				return cls(self.__dict__.get(key, _def))
			else:
				raise ValueError()

		return self.__dict__.__getitem__(key)
	def __setitem__(self, __key : str, __value : ValueType):
		return self.__dict__.__setitem__(__key, __value)
	def __iter__(self):
		return self.__dict__.__iter__()
	def __contains__(self, __key):
		return self.__dict__.__contains__(__key)
	
	def __export__(self) -> AttrDict:
		return self.__dict__.copy()
	
class HeaderArchetype(Header):
	_entries : ClassVar[Dict[str, Type[ValueType]]] = {}

	def __init__(self, source : Header | Dict[str, ValueType]):
		super().__init__('', {key : source[key] for key in (_min_required | HeaderArchetype._entries).keys()} )
		
		axes = cast(int, self['NAXIS'])
		axes_n = tuple(int(source[f'NAXIS{n + 1}']) for n in range(axes))
		for n in range(axes):
			self[f'NAXIS{n+1}'] = axes_n[n]
	
	def validate(self, header : Header, failed : Optional[Callable[[str, ValueType, ValueType], None]] = None) -> bool:
		for key, value in self.items():
			if (key not in header.keys()) or (header[key] != value):
					if callable(failed): 
						failed(key, value, header[key])
					return False
		return True

	@staticmethod
	def set_keywords(user_keys : Dict[str, type]):
		assert all([ type(key) is str  for key in user_keys])
		assert all([ value in (int, bool, float, str) for value in user_keys.values()])
		HeaderArchetype._entries = user_keys
	
	@classmethod
	def __import__(cls, attributes: AttrDict, **cls_kw : Any) -> Self:
		return cls(attributes)

class FileInfo(NamedTuple, STObject):	#type: ignore[misc]
	path : str
	relative_path : bool
	header : Header
	get_data : _bound_reader

	@classmethod
	def new(cls, file_path : str, relative_path : bool | None = None) -> Self:
		if relative_path is not None:
			is_rel = relative_path
		else:
			is_rel = not os.path.isabs(file_path)
		
		if is_rel and _EXPORT_PATH:
			abs_path = os.path.join(_EXPORT_PATH, file_path)
		else:
			abs_path = os.path.abspath(file_path)

		norm_path = abs_path.replace('\\', '/')
		_h_dict = {key.rstrip() : value for key, value in _get_header(abs_path)}
		header_obj = Header(norm_path, _h_dict)
		bound_reader = _bound_reader(abs_path, header_obj.shape, 
											(header_obj['BSCALE', int, 0], header_obj['BZERO', int, 0]), header_obj['BITPIX', int]) 
		
		return cls(norm_path, is_rel, header_obj, bound_reader)
	
	@property
	def name(self) -> str:
		return os.path.basename(self.path)
	
	@property
	def bytes(self) -> int:
		return os.path.getsize(self.path)
	
	@classmethod
	def __import__(cls, attributes: AttrDict, **cls_kw : Any) -> FileInfo:
		return FileInfo.new(attributes['path'], attributes['relative_path'])
	
	def __export__(self) -> AttrDict:
		if self.relative_path and _EXPORT_PATH:
			path = os.path.relpath(self.path, _EXPORT_PATH)
		else:
			path = self.path
		return {'path' : path.replace("\\", "/"), 'relative_path' : self.relative_path}
	
	def __pprint__(self, indent: int, fold: int) -> str:
		if fold == 0:
			return type(self).__name__ + f': {self.name}'
		indentation = spaces * (2*indent + 1)
		string = [spaces * (2*indent) + type(self).__name__ + f' {self.name}:']
		string.append(indentation + f'path: "{self.path}"')

		if self.bytes < 1024:
			string.append(indentation + f'size: {self.bytes} bytes')
		elif self.bytes < 1048576:
			string.append(indentation + f'size: {self.bytes/1024:.2f} KB')
		else:
			string.append(indentation + f'size: {self.bytes/1048576:.2f} MB')
		
		if indent + 1 < fold:
			string.append(indentation + 'header: ' + self.header.__pprint__(indent + 1, fold))
		else:
			string.append(indentation + 'header: Header')
		if indent != 0:
			string.insert(0, '')
		return '\n'.join(string)
	
	def __str__(self) -> str:
		return self.__pprint__(0, 1)
	def __repr__(self) -> str:
		return self.__pprint__(0, 0)
	def __eq__(self, __value):
		if not isinstance(__value, FileInfo): 
			return False
		return self.path == __value.path
	def __hash__(self) -> int:
		return hash(self.path)

#region Photometry
class FluxInfo(NamedTuple):
	value: float
	sigma: float
	raw: float = 0
	max: float = 0

	def __repr__(self) -> str:
		return str(self.value)
	def __add__(self, other : tuple | float | int) -> float: # type: ignore[override]
		if isinstance(other, tuple):	raise NotImplementedError()
		return self.value + other
	def __sub__(self, other :  float | int) -> float:
		return self.value - other
	def __mul__(self, other :  float | int | Any) -> float: # type: ignore[override]
		if not isinstance(other, (int, float)): raise NotImplementedError()
		return self.value * other
	def __truediv__(self, other :  float | int) -> float:
		return self.value / other
	def __radd__(self, other :  float | int):
		return self.__add__(other)
	def __rsub__(self, other :  float | int) -> float:
		return self.__sub__(other)
	def __rmul__(self, other :  float | int) -> float: # type: ignore[override]
		return self.__mul__(other)
	def __array__(self):
		return np.array(self.value)

class ApertureInfo(NamedTuple):
	radius: float
	width: float
	offset: float

class PhotometryResult(NamedTuple, STObject):	#type: ignore[misc]
	method: str
	flux : FluxInfo
	background : FluxInfo
	aperture_info : ApertureInfo
	psf_parameters: Optional[Tuple[float, float, float]] = None

	@classmethod
	def new(cls, *,
		method: str,
		flux: float,
		flux_sigma: float,
		flux_raw: float,
		flux_max: float,
		background: float,
		background_sigma: float,
		background_max: float,
		aperture_radius: float,
		annulus_width: float,
		annulus_offset: float,
		psf_parameters: Optional[Tuple[float, float, float]] = None,
	):
		return cls(method, FluxInfo(flux, flux_sigma, flux_raw, flux_max),
						FluxInfo(background, background_sigma, background_max), ApertureInfo(aperture_radius, annulus_width, annulus_offset), psf_parameters)
	@classmethod
	def zero(cls):
		return cls('None', FluxInfo(0, 0, 0, 0), FluxInfo(0, 0), ApertureInfo(0, 0, 0))
	

	@property
	def snr(self) -> float:
		return self.flux.value / self.background.value
	@property
	def error(self) -> float:
		return math.sqrt(self.flux.sigma**2 + self.background.sigma**2)
	
	def __export__(self) -> AttrDict:
		attrs = {
			'flux' : self.flux.value,
			'flux_sigma' : self.flux.sigma,
			'flux_raw' : self.flux.raw,
			'flux_max' : self.flux.max,
			'background' : self.background.value,
			'background_sigma' : self.background.sigma,
			'background_max' : self.background.max,
			'phot_method' : self.method,
			'aperture_params' : tuple(self.aperture_info)
		}
		if self.psf_parameters:
			attrs['psf_params'] = self.psf_parameters
		return attrs
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		flux = FluxInfo(attributes['flux'], attributes['flux_raw'], attributes['flux_sigma'], attributes['flux_max'])
		backg = FluxInfo(attributes['background'], attributes['background_sigma'], attributes['background_max'])
		apert = ApertureInfo(*attributes['aperture_params'])
		return cls(attributes['phot_method'], flux, backg, apert, attributes.get('psf_params', None))
	
	def __str__(self) -> str:
		return self.__pprint__(0, 1)
	def __repr__(self) -> str:
		return self.__pprint__(0, 0)
	
	def __pprint__(self, indent: int, fold : int) -> str:
		if fold == 0:
			return type(self).__name__ + f' {self.flux.value:.2f} ± {self.flux.sigma:.2f}'
		indentation = spaces * (2*indent + 1)
		string = [spaces * (2*indent) + type(self).__name__ + ':'
					,indentation + f'method:     {self.method}'
					,indentation + f'flux:       {self.flux.value:.2f} ± {self.flux.sigma:.2f}'
					,indentation + f'background: {self.background.value:.2f} ± {self.background.sigma:.2f}'
					,indentation + f'error:      {self.error:.3f}']
		if indent != 0:
			string.insert(0, '')
		return '\n'.join(string)
	
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
		return self.photometry.flux.value
	
	def __export__(self) -> AttrDict:
		return super().__export__()
	
	@classmethod
	def __import__(cls, attributes: AttrDict, **cls_kw : Any) -> Self:
		params = ('name', 'position', 'aperture', 'photometry')
		attributes = {k: attributes[k] for k in params if k in attributes}
		return cls(**attributes)

class ReferenceStar(Star):
	magnitude : float = 0

#endregion
#region Tracking

_Radians = float
class TrackingSolution(NamedTuple, STObject):	#type: ignore[misc]
	method : str
	translation : Position
	rotation_matrix : Matrix2x2
	error : float
	lost : Optional[List[int]]

	@classmethod
	def compute(cls,method : str,
						start_pos : ArrayLike | PositionArray,
						new_pos : ArrayLike | PositionArray,*,
						weights : Optional[ArrayLike] = None,
						lost_indices : List[int] = [],
						rejection_iter : int = 1,
						rejection_sigma : float = 3) -> Self:

		start_arr = PositionArray( *start_pos)
		new_arr = PositionArray( *new_pos)

		if weights:
			weights_arr = Array( *weights)
		else: 
			weights_arr = None

		mask = list(range(len(start_arr)))
		displacements = new_arr - start_arr
		residuals = displacements - average(displacements)

		r_count, r_error = 0, 0.
		for i in range(rejection_iter):
			if len(mask) == 0:
				print('Solution did not converge')
				return TrackingSolution.identity(method)
			if len(mask) < 3:
				print('SVD with less than three tracked stars may not converge')
			
			variance = average([ pos.sq_length for pos in residuals[mask] ])

			for j, res in enumerate(residuals):
				if j not in mask:
					continue
				if (err := res.sq_length) > max(rejection_sigma * variance, 1):
					mask.remove(j)
					lost_indices.append(j)
					r_error += err; r_count += 1
			if r_count > 0:
				print(f'{r_count} stars deviated from the solution with average displacement error: {math.sqrt(r_error/r_count):.2f}px (iter {i+1})')

		start_masked = start_arr[mask]
		new_masked = new_arr[mask]
		weights_masked = weights_arr[mask] if weights_arr else None
		centroid_start =  average(start_masked, weights_masked)
		centroid_new =   average(new_masked, weights_masked)

		H_matrix = outer(start_masked - centroid_start, new_masked - centroid_new)
		_, U_matrix, V_matrix = SVD(H_matrix)
		R_matrix = V_matrix.transpose * U_matrix
		delta_pos = centroid_new - R_matrix * centroid_start

		transformed_points = PositionArray( *[ (R_matrix * pos) + delta_pos for pos in start_masked] )
		reprojection_error = math.sqrt(average( [diff.sq_length for diff in transformed_points - new_masked] ))
		return cls(method, delta_pos, R_matrix, reprojection_error, lost_indices)

	@classmethod
	def new(cls,method : str,
					translation : Position, rotation : _Radians,
					error : float, lost_indices : Optional[List[int]] = None) -> Self:
		a = math.cos(rotation)
		b = math.sin(rotation)
		return cls(method, translation, Matrix2x2(a, -b, b, a), error, lost_indices)

	@classmethod
	def identity(cls, method : str = 'None'):
		return cls(method, Position(0, 0), Matrix2x2.identity(), 0, None)
	
	@property
	def matrix(self) -> Matrix3x3:
		dx, dy = self.translation
		a, b, c, d = self.rotation_matrix
		return Matrix3x3(
			a, b, dx  ,
			c, d, dy  ,
			0, 0, 1   )  
	
	@property	
	def rotation(self) -> float:
		return math.degrees(math.acos(self.rotation_matrix.a))
	
	def transform(self, pos : Position) -> Position:
		return (self.rotation_matrix * pos) + self.translation
	
	def __export__(self) -> AttrDict:
		return {
			'method': self.method,
			'translation': self.translation,
			'rotation' : self.rotation,
			'error' : self.error,
			'lost_indices' : self.lost }
	@classmethod
	def __import__(cls, attributes: AttrDict) -> TrackingSolution:
		translation = Position.new(attributes['translation'])
		rot_rad = math.radians(attributes['rotation'])
		return TrackingSolution.new(attributes['method'], translation, rot_rad, attributes['error'], attributes['lost_indices'])
	
	def __str__(self) -> str:
		return self.__pprint__(0, 1)
	def __repr__(self) -> str:
		return self.__pprint__(0, 0)
	
	def __pprint__(self, indent: int, fold : int) -> str:
		translation = f'{self.translation.x:.1f} px, {self.translation.x:.1f} px'
		if fold == 0:
			return type(self).__name__ + f' {translation}, {self.rotation:.2f}°'
		
		indentation = spaces * (indent + 1)
		string = [spaces * (2*indent) + type(self).__name__ +':'
					,indentation + f'method:      {self.method}'
					,indentation + f'translation: {translation}'
					,indentation + f'rotation:    {self.rotation:.2f}°'
					,indentation + f'error:       {self.error:.3f} px']
		if indent != 0:
			string.insert(0, '')
		return '\n'.join(string)
#endregion

# Trick to communicate between Session and FileInfo during the Import process
class SessionLocationBlock(NamedTuple, STObject): #type: ignore[misc]
	session_path : str
	uses_relative : bool

	@classmethod
	def __import__(cls, attributes: AttrDict, **cls_kw: Any) -> Self:
		RelativeContext.set(attributes['session_path'])
		return cls(attributes['session_path'], attributes['uses_relative'])
	
	def __export__(self) -> AttrDict:
		return {'session_path': self.session_path, 'uses_relative': self.uses_relative}
	
	def __pprint__(self, indent: int, fold: int) -> str:
		if fold == 0:
			return self.session_path
		string = ['',spaces * (2*indent + 1) + 'path: ' + self.session_path,
					 spaces * (2*indent + 1) + 'uses_relative: ' + str(self.uses_relative)]
		return '\n'.join(string)

_register_class(FileInfo)
_register_class(TrackingSolution)
_register_class(PhotometryResult)
_register_class(SessionLocationBlock)



