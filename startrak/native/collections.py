# compiled

from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from typing import Any, ClassVar, Collection, Iterable, Iterator, List, Literal, NamedTuple, Never, Optional, Self, Dict, Sized, Tuple, Union, overload

PositionLike = Union[Tuple[float|Any, ...], Tuple[float|Any, float|Any], List[float|Any], NDArray[np.float_]]
_IndexLike = int | bool 
_IndexLike_n =  np.int_ | np.bool_
_MaskLike = List[_IndexLike] | NDArray[_IndexLike_n]
_LiteralAxis = Literal['x', 0, 'y', 1, 'all', ':']

class Position(NamedTuple):
	x : float
	y : float

	@classmethod 
	def new(cls, value : Position | PositionLike, is_rc : bool = False) -> Position:
		err_msg = f"Only size 2 {type(value).__name__} can be converted into Position"
		
		if type(value) is Position:
			return value 
		elif (type(value) is tuple) or (type(value) is list) or (isinstance(value, np.ndarray)):
			if len(value) != 2:
				raise ValueError(err_msg)
			if not is_rc:
				return Position(value[0], value[1])
			else:
				return Position(value[1], value[0])
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
	
	def __add__(self, other : Position | PositionLike,/) -> Position:
		if len(other) != 2: raise ValueError(other)
		return Position(self[0] + other[0], self[1] + other[1])
	
	def __sub__(self, other : Position | PositionLike, /) -> Position:
		if len(other) != 2: raise ValueError(other)
		return Position(self.x - other[0], self.y - other[1])
	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.array(self[:])
	
	def __array_wrap__(self, out_arr : NDArray[np.float_], context= None):
		return Position(out_arr[0], out_arr[1])
	
	def __str__(self) -> str:
		return f'[{self.x:.1f}, {self.y:.1f}]'
	
class PositionArray:
	_list : List[Position]
	def __init__(self, positions: Iterable[Position|PositionLike]|None = None):
		if positions is None:
			self._list = list[Position]()
		else:
			self._list = [Position.new(pos) for pos in positions]

	@property
	def x(self) -> List[float]:
		return [pos.x for pos in self._list]
	@property
	def y(self) -> List[float]:
		return [pos.y for pos in self._list]
	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.vstack(self._list)
	def __len__(self) -> int:
		return len(self._list)
	
	#region getter and setter
	@overload
	def __getitem__(self, index : int) -> Position: ...
	@overload
	def __getitem__(self, index : slice | _MaskLike) -> PositionArray: ...
	@overload
	def __getitem__(self, index : Tuple[int, Literal['x', 'y', 0, 1]]) ->  float: ...
	@overload
	def __getitem__(self, index : Tuple[slice, Literal['x', 'y', 0, 1]]) ->  List[float]: ...
	@overload
	def __getitem__(self, index : Tuple[int, Literal['all', ':']]) ->  Position: ...
	@overload
	def __getitem__(self, index : Tuple[slice, Literal['all', ':']]) ->  PositionArray: ...
	
	def __getitem__(self, index : int | slice | _MaskLike | Tuple[int|slice, _LiteralAxis]) -> Position | PositionArray | List[float] | float:
		if type(index) is int:
			return self._list[index]
		
		elif type(index) is slice:
			return PositionArray(self._list[index])
		
		elif type(index) is tuple:
			if len(index) != 2:
				raise ValueError(index)
			if type(index[0]) is int:
				if index[1] == 'all' or index[1] == ':':
					return self._list[index[0]]
				elif index[1] == 'x' or index[1] == 0:
					return self._list[index[0]].x
				elif index[1] == 'y' or index[1] == 1:
					return self._list[index[0]].y
				else:
					raise ValueError(index[1])

			elif type(index[0]) is slice:
				if index[1] == 'all' or index[1] == ':':
					return PositionArray(self._list[index[0]])
				elif index[1] == 'x' or index[1] == 0:
					return [pos.x for pos in self._list[index[0]]]
				elif index[1] == 'y' or index[1] == 1:
					return [pos.y for pos in self._list[index[0]]]
				else:
					raise ValueError(index[1])
			else:
				raise ValueError("Only 'int' and 'slice' can be used with 2D indexing")
		
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
			elif isinstance(index[0], np.integer):
				return PositionArray([self._list[i] for i in index ])
			else:
				raise ValueError(type(index[0]))
		
		else:
			raise ValueError(type(index))

	def __setitem__(self, index : int, value : Position):
		if type(value) is tuple:
			value = Position(value[0], value[1])
		self._list[index] = value
#endregion

	def __add__(self, other : PositionArray | Position | PositionLike):
		if type(other) is PositionArray:
			return PositionArray([ a + b for a,b in zip(self._list, other._list)])
		elif isinstance(other, Position) or isinstance(other, tuple|list|np.ndarray):
			return PositionArray( [a + other for a in self._list] )
		else:
			raise ValueError(type(other))
	
	def __sub__(self, other : PositionArray | Position | PositionLike):
		if type(other) is PositionArray:
			return PositionArray([ a - b for a,b in zip(self._list, other._list)])
		elif isinstance(other, Position) or isinstance(other, tuple|list|np.ndarray):
			return PositionArray( [a - other for a in self._list] )
		else:
			raise ValueError(type(other))
	
	def __contains__(self, value : Position) -> bool:
		return value in self._list
	def __iter__(self) -> Iterator[Position]:
		return self._list.__iter__()
	def __repr__(self) -> str:
		return 'PositionArray:\n' + '  \n'.join(map(str, self._list))

	#region List methods
	def append(self, value: Position): 
		if type(value) is tuple:
			value = Position(value[0], value[1])
		self._list.append(value)
	
	def extend(self, positions: List[Position] | PositionArray): 
		if type(positions) is PositionArray:
			self._list.extend(positions._list)
		else:
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
	#endregion