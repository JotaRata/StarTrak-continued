# compiled

from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from typing import Any, Iterable, List, Literal, NamedTuple, Sequence, Tuple, Union, overload
from startrak.native.alias import MaskLike
from startrak.native.ext import STCollection

PositionLike = Union[Tuple[float|Any, ...], Tuple[float|Any, float|Any], List[float|Any], NDArray[np.float_]]
_MatrixLike3x3 = NDArray[np.floating] | List[List | Tuple | NDArray] | Tuple[List | Tuple | NDArray, ...]
_LiteralAxis = Literal['x', 0, 'y', 1]


class Position(NamedTuple):
	x : float
	y : float

	@classmethod 
	def new(cls, value : Position | PositionLike, is_rc : bool = False) -> Position:
		if type(value) is Position:
			return value 
		
		assert len(value) == 2, f"Only size 2 {type(value).__name__} can be converted into Position"
		if (type(value) is tuple) or (type(value) is list):
			if not is_rc:
				return Position(value[0], value[1])
			return Position(value[1], value[0])
		
		elif isinstance(value, np.ndarray):
			_value : List[float] = value.tolist()
			if not is_rc:
				return Position(_value[0], _value[1])
			else:
				return Position(_value[1], _value[0])

		else:
			raise TypeError(type(value))
	
	@property
	def rc(self) -> list[int]:
		r = np.round(self)
		return [r[1], r[0]]
	
	@property
	def sarray(self) -> NDArray[np.float_]:
		dt = np.dtype([('x', 'float'), ('y', 'float')])
		return np.array(self[:], dtype= dt)
	
	def transform(self, matrix : _MatrixLike3x3) -> Position:
		assert len(matrix) == 3, f'Transformation matrix must have 3 rows (got {len(matrix)}).'
		assert len(matrix[0]) == 3, f'Transformation matrix must have 3 columns (got {len(matrix[0])}).'

		vector = (*self, 1)
		result = [0, 0]
		# Perform the matrix-vector multiplication
		result[0] = matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2]
		result[1] = matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2]
		return Position(*result)
	
	def __add__(self, other : Position | PositionLike | Any,/) -> Position:
		if other == 0:
			return self
		if not isinstance(other, Position):
			assert isinstance(other, Sequence), 'Not a sequence'
			assert len(other) == 2, 'Cannot coherce 2D Position with Sequence of length different than 2'
		return Position(self[0] + other[0], self[1] + other[1])
	
	def __sub__(self, other : Position | PositionLike | Any, /) -> Position:
		if not isinstance(other, Position):
			assert isinstance(other, Sequence), 'Not a sequence'
			assert len(other) == 2, 'Cannot coherce 2D Position with Sequence of length different than 2'
		return Position(self.x - other[0], self.y - other[1])
	
	def __radd__(self, other : Position | PositionLike | Any,/) -> Position:
		return self.__add__(other)
	
	def __mul__(self, other : Position | PositionLike | Any, /) -> Position:
		if isinstance(other, float | int):
			return Position(self.x * other, self.y * other)
		if not isinstance(other, Position):
			assert isinstance(other, Sequence), 'Not a sequence'
			assert len(other) == 2, 'Cannot coherce 2D Position with Sequence of length different than 2'
		return Position(self.x * other[0], self.y * other[1])
	
	def __truediv__(self, other : Position | PositionLike | Any, /) -> Position:
		if isinstance(other, float | int):
			return Position(self.x / other, self.y / other)
		if not isinstance(other, Position):
			assert isinstance(other, Sequence), 'Not a sequence'
			assert len(other) == 2, 'Cannot coherce 2D Position with Sequence of length different than 2'
		return Position(self.x / other[0], self.y / other[1])

	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.array(self[:])
	
	def __array_wrap__(self, out_arr : NDArray[np.float_], context= None):
		return Position(out_arr[0], out_arr[1])
	
	def __str__(self) -> str:
		return f'({self.x:.1f}, {self.y:.1f})'
	
class PositionArray(STCollection[Position]):
	_cached_y : List[float] | None
	_cached_x : List[float] | None

	def __init__(self, *positions: Position | PositionLike):
		self._closed = False
		self._cached_y = None
		self._cached_x = None
		
		self._internal = [Position.new(pos) for pos in positions]
	@property
	def is_closed(self) -> bool:
		return super().is_closed

	@property
	def x(self) -> List[float]:
		if self._cached_x is None:
			self._cached_x = [pos.x for pos in self._internal]
		return self._cached_x
	@property
	def y(self) -> List[float]:
		if self._cached_y is None:
			self._cached_y =  [pos.y for pos in self._internal]
		return self._cached_y
	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.vstack(self._internal)
	
	@overload
	def __getitem__(self, index : int) -> Position: ...
	@overload
	def __getitem__(self, index : slice | MaskLike) -> PositionArray: ...
	@overload
	def __getitem__(self, index : Tuple[int, Literal['x', 'y', 0, 1]]) ->  float: ...
	@overload
	def __getitem__(self, index : Tuple[slice, Literal['x', 'y', 0, 1]]) ->  List[float]: ...

	def __getitem__(self, index : int | slice | MaskLike | Tuple[int|slice, _LiteralAxis]) -> Position | PositionArray | List[float] | float:
		if type(index) is tuple:
			assert len(index) == 2
			idx, axis = index
			if type(idx) is int or type(idx) is slice:
				match axis:
					case 'x' | 0:
						return self.x[idx]
					case 'y' | 1:
						return self.y[idx]
					case _:
						raise ValueError(type(axis))
			else:
				raise ValueError("Only 'int' and 'slice' can be used with 2D indexing")
			
		else: assert not isinstance(index, tuple)
		return super().__getitem__(index)
	
	def __setitem__(self, index: int, value: PositionLike | Position):
		if type(value) is not Position:
			value = Position(value[0], value[1])
		self.trim()
		return super().__setitem__(index, value)
#endregions

	def __add__(self, other : PositionArray | Position | PositionLike):
		if type(other) is PositionArray:
			return PositionArray( *[a + b for a,b in zip(self._internal, other._internal)] )
		elif isinstance(other, Position) or isinstance(other, tuple|list|np.ndarray):
			return PositionArray( *[a + other for a in self._internal] )
		else:
			raise ValueError(type(other))
	
	def __sub__(self, other : PositionArray | Position | PositionLike):
		if type(other) is PositionArray:
			return PositionArray( *[ a - b for a,b in zip(self._internal, other._internal)])
		elif isinstance(other, Position) or isinstance(other, tuple|list|np.ndarray):
			return PositionArray( *[a - other for a in self._internal] )
		else:
			raise ValueError(type(other))

	def append(self, value: PositionLike | Position):
		if type(value) is not Position:
			value = Position(value[0], value[1])
		return super().append(value)	
	def insert(self, index: int, value: PositionLike | Position):
		if type(value) is not Position:
			value = Position(value[0], value[1])
		return super().insert(index, value)

	def __on_change__(self):
		self.trim()
		return super().__on_change__()
	
	def trim(self):
		self._cached_x =  None
		self._cached_y =  None
