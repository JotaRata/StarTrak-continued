# compiled

from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from typing import Any, ClassVar, Collection, Iterable, List, NamedTuple, Self, Dict, Tuple, overload
from startrak.native.alias import PositionLike


class Position(NamedTuple):
	x : int
	y : int

	@classmethod 
	def new(cls, value : Position | PositionLike, is_rc : bool = False) -> Position:
		err_msg = f"Only size 2 {type(value).__name__} can be converted into Position"
		
		if type(value) is Position:
			return value 
		elif type(value) is tuple or type(value) is list:
			if len(value) != 2:
				raise ValueError(err_msg)
			if not is_rc:
				return Position(value[0], value[1])
			else:
				return Position(value[1], value[0])
		elif isinstance(type(value), np.ndarray):
			if len(value) != 2:
				raise ValueError(err_msg)
			_int = np.round(value).astype(np.int_)
			if not is_rc:
				return Position(_int[0], _int[1])
			else:
				return Position(_int[1], _int[0])
		else:
			raise TypeError(type(value))
			
	def rc(self) -> NDArray[np.int_]:
		return np.array(self[::-1])
	
	def __add__(self, other : Position | Tuple[int|Any,...],/) -> Position:
		if len(other) != 2: raise ValueError(other)
		return Position(self[0] + other[0], self[1] + other[1])
	
	def __sub__(self, other : Position) -> Position:
		return Position(self.x - other.x, self.y - other.y)
	def __array__(self, dtype=None) -> NDArray[np.int_]:
		return np.array(self[:], dtype= np.int_)
	def __array_wrap__(self, out_arr : NDArray[np.int_], context= None):
		rounded = np.round(out_arr).astype(np.int_)
		return Position(rounded[0], rounded[1])
	
class PositionArray:
	_list : List[Position]
	def __init__(self, positions: Iterable[Position]):
		self._list = list(positions)

	def __array__(self, dtype=None) -> NDArray[np.int_]:
		return np.vstack(self._list, dtype= np.int_)
	def __len__(self) -> int:
		return len(self._list)
	def __getitem__(self, index : int) -> Position:
		return self._list[index]
	def __setitem__(self, index : int, value : Position):
		self._list[index] = value
	def __contains__(self, value : Position) -> bool:
		return value in self._list

	def append(self, position: Position): 
		self._list.append(position)
	
	def extend(self, positions: List[Position]): 
		self._list.extend(positions)
	
	def insert(self, index: int, position: Position): 
		self._list.insert(index, position)
	
	def remove(self, position: Position): 
		self._list.remove(position)
	
	def pop(self, index: int) -> Position: 
		return self._list.pop(index)
	
	def clear(self): 
		self._list.clear()
	
	def index(self, position: Position, start: int = 0, end: int = 0) -> int:
		return self._list.index(position, start, end)
	
	def reverse(self): 
		self._list.reverse()
	def copy(self) -> "PositionArray":
		return PositionArray(self._list.copy())
