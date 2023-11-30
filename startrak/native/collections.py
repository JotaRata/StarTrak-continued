# compiled

from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from typing import Any, ClassVar, Collection, Iterable, Iterator, List, NamedTuple, Self, Dict, Sized, Tuple, Union, overload

PositionLike = Tuple[float, ...] | Tuple[float, float] | List[float] | NDArray[np.float_]
_IndexLike = int | bool 
_IndexLike_n =  np.int_ | np.bool_
_MaskLike = List[_IndexLike] | NDArray[_IndexLike_n]

class Position(NamedTuple):
	x : float
	y : float

	@classmethod 
	def new(cls, value : Position | PositionLike, is_rc : bool = False) -> Position:
		err_msg = f"Only size 2 {type(value).__name__} can be converted into Position"
		
		if type(value) is Position:
			return value 
		elif type(value) is tuple or type(value) is list or isinstance(type(value), np.ndarray):
			if len(value) != 2:
				raise ValueError(err_msg)
			if not is_rc:
				return Position(value[0], value[1])
			else:
				return Position(value[1], value[0])
		else:
			raise TypeError(type(value))
			
	def rc(self) -> list[int]:
		r = np.round(self)
		return [r[1], r[0]]
	def sarray(self, dtype=None) -> NDArray[np.float_]:
		dt = np.dtype([('x', 'float'), ('y', 'float')])
		return np.array(self[:], dtype= dt)
	
	def __add__(self, other : Position | Tuple[float|Any,...],/) -> Position:
		if len(other) != 2: raise ValueError(other)
		return Position(self[0] + other[0], self[1] + other[1])
	
	def __sub__(self, other : Position) -> Position:
		if len(other) != 2: raise ValueError(other)
		return Position(self.x - other.x, self.y - other.y)
	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.array(self[:])
	
	def __array_wrap__(self, out_arr : NDArray[np.float_], context= None):
		return Position(out_arr[0], out_arr[1])
	
	def __str__(self) -> str:
		return f'[{self.x}, {self.y}]'
	
class PositionArray:
	_list : List[Position]
	def __init__(self, positions: Iterable[Position]):
		self._list = [Position.new(pos) for pos in positions]

	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.vstack(self._list)
	def __len__(self) -> int:
		return len(self._list)
	
	@overload
	def __getitem__(self, index : int) -> Position: ...
	@overload
	def __getitem__(self, index : slice | _MaskLike) -> PositionArray: ...
	
	def __getitem__(self, index : int | slice | _MaskLike) -> Position | PositionArray:
		if type(index) is int:
			return self._list[index]
		elif type(index) is slice:
			return PositionArray(self._list[index])
		elif type(index) is list:
			if type(index[0]) is bool:
				if (l1:=len(index)) != (l2:=len(self)): raise IndexError(f"Sizes don't match, got {l1}, expected{l2}")
				return PositionArray([pos for i, pos in enumerate(self._list) if index[i] ])
			elif type(index[0]) is int:
				return PositionArray([self._list[i] for i in index ])
			else:
				raise ValueError(type(index[0]))
		elif isinstance(index, np.ndarray):
			if isinstance(index[0], np.bool_):
				if (l1:=len(index)) != (l2:=len(self)): raise IndexError(f"Sizes don't match, got {l1}, expected{l2}")
				return PositionArray([pos for i, pos in enumerate(self._list) if index[i] ])
			elif isinstance(index[0], np.int_):
				return PositionArray([self._list[i] for i in index ])
			else:
				raise ValueError(type(index[0]))
		else:
			raise ValueError(type(index))

	def __setitem__(self, index : int, value : Position):
		if type(value) is tuple:
			value = Position(value[0], value[1])
		self._list[index] = value
	def __contains__(self, value : Position) -> bool:
		return value in self._list
	def __iter__(self) -> Iterator[Position]:
		return self._list.__iter__()
	def __repr__(self) -> str:
		return '\n'.join(map(str, self._list))

	def append(self, value: Position): 
		if type(value) is tuple:
			value = Position(value[0], value[1])
		self._list.append(value)
	
	def extend(self, positions: List[Position]): 
		self._list.extend(positions)
	
	def insert(self, index: int, value: Position): 
		if type(value) is tuple:
			value = Position(value[0], value[1])
		self._list.insert(index, value)
	
	def remove(self, position: Position): 
		self._list.remove(position)
	
	def pop(self, index: int) -> Position: 
		return self._list.pop(index)
	
	def clear(self): 
		self._list.clear()
	
	def reverse(self): 
		self._list.reverse()
	def copy(self) -> "PositionArray":
		return PositionArray(self._list.copy())
