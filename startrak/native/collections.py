# compiled

from __future__ import annotations
from abc import ABC, abstractmethod, abstractproperty
import numpy as np
from numpy.typing import NDArray
from typing import Any, ClassVar, Collection, Generic, Iterable, Iterator, List, Literal, NamedTuple, Never, Optional, Self, Dict, Sized, Tuple, TypeVar, Union, overload

PositionLike = Union[Tuple[float|Any, ...], Tuple[float|Any, float|Any], List[float|Any], NDArray[np.float_]]
_IndexLike = int | bool 
_IndexLike_n =  np.int_ | np.bool_
_MaskLike = List[_IndexLike] | NDArray[_IndexLike_n]
_LiteralAxis = Literal['x', 0, 'y', 1, 'all', ':']

TList = TypeVar('TList')
class STCollection(ABC, Generic[TList]):
	_internal : List[TList]
	_closed : bool

	def __init__(self, values : Iterable[TList] | None = None ):
		self._closed = False
		if values is None:
			self._internal = list[TList]()
		else:
			self._internal = list[TList](values)

	@abstractproperty
	def is_closed(self) -> bool:
		return self._closed
	
	def close(self):
		self._closed = True

	def __clexc__(self):
		if self._closed:
			raise KeyError(self.__class__.__name__ + ' is marked as closed.')

	def __iter__(self) -> Iterator[TList]:
		return self._internal.__iter__()
	def __len__(self) -> int:
		return self._internal.__len__()
	def __contains__(self, value : TList) -> bool:
		return self._internal.__contains__(value)
	
	def __add__(self, other : Self | TList) -> Self:
		raise NotImplementedError(f"Operator '+' is not defined for type {type(self).__name__}")
	def __sub__(self, other : Self | TList) -> Self:
		raise NotImplementedError(f"Operator '-' is not defined for type {type(self).__name__}")
	def __mul__(self, other : Self | TList) -> Self:
		raise NotImplementedError(f"Operator '*' is not defined for type {type(self).__name__}")

	@overload
	def __getitem__(self, index : int ) ->  TList: ...
	@overload
	def __getitem__(self, index :  slice | _MaskLike) -> Self: ...

	def __getitem__(self, index : int | slice | _MaskLike) -> Self | TList:
		cls = self.__class__
		if type(index) is int:
			return self._internal[index]
		
		elif type(index) is slice:
			return cls(self._internal[index])
		
		# case: index list or boolean mask
		elif type(index) is list:
			if len(index) == 0:
				return cls()
			if type(index[0]) is bool:
				if (l1:=len(index)) != (l2:=len(self)): raise IndexError(f"Sizes don't match, got {l1}, expected{l2}")
				return cls([pos for i, pos in enumerate(self._internal) if index[i] ])
			elif type(index[0]) is int:
				return cls([self._internal[i] for i in index ])
			else:
				raise ValueError(type(index[0]))
		
		elif isinstance(index, np.ndarray):
			if len(index) == 0:
				return cls()
			if isinstance(index[0], np.bool_):
				if (l1:=len(index)) != (l2:=len(self)): raise IndexError(f"Sizes don't match, got {l1}, expected{l2}")
				return cls([pos for i, pos in enumerate(self._internal) if index[i] ])
			elif isinstance(index[0], np.integer):
				return cls([self._internal[int(i)] for i in index ])
			else:
				raise ValueError(type(index[0]))
		else:
			raise ValueError(type(index))

	def __setitem__(self, index : int, value : TList):
		self.__clexc__()
		return self._internal.__setitem__(index, value)

	def append(self, value: TList): 
		self.__clexc__()
		self._internal.append(value)
	
	def extend(self, values: Self | Iterable[TList]): 
		self.__clexc__()
		return self._internal.extend(values)
	
	def insert(self, index: int, value: TList): 
		self.__clexc__()
		self._internal.insert(index, value)
	
	def remove(self, value: TList): 
		self.__clexc__()
		self._internal.remove(value)
	
	def pop(self, index: int) -> TList: 
		self.__clexc__()
		return self._internal.pop(index)
	
	def clear(self): 
		self.__clexc__()
		self._internal.clear()
	
	def reverse(self): 
		self.__clexc__()
		self._internal.reverse()
	def copy(self) -> Self:
		return type(self)(self._internal.copy())
	
	def __pprint__(self, indent : int = 0) -> str:
		sp = '  '
		_ind = sp * (indent + 1)
		_str = ['', sp*indent + self.__class__.__name__ + f':  ({self.__len__()} entries)']
		for value in self.__iter__():
			_str.append(_ind + f'{str(value)}')
		return '\n'.join(_str)
	def __str__(self) -> str:
		return self.__pprint__()
	
	def __repr__(self) -> str:
		return self.__str__()


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
	
class PositionArray(STCollection[Position]):
	def __init__(self, positions: Iterable[Position] | Iterable[PositionLike] | None = None):
		self._closed = False
		if positions is None:
			self._internal = list[Position]()
		else:
			self._internal = [Position.new(pos) for pos in positions]
	@property
	def is_closed(self) -> bool:
		return super().is_closed

	@property
	def x(self) -> List[float]:
		return [pos.x for pos in self._internal]
	@property
	def y(self) -> List[float]:
		return [pos.y for pos in self._internal]
	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.vstack(self._internal)
	
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
		if type(index) is tuple:
			if len(index) != 2:
				raise ValueError(index)
			if type(index[0]) is int:
				if index[1] == 'all' or index[1] == ':':
					return self._internal[index[0]]
				elif index[1] == 'x' or index[1] == 0:
					return self._internal[index[0]].x
				elif index[1] == 'y' or index[1] == 1:
					return self._internal[index[0]].y
				else:
					raise ValueError(index[1])

			elif type(index[0]) is slice:
				if index[1] == 'all' or index[1] == ':':
					return PositionArray(self._internal[index[0]])
				elif index[1] == 'x' or index[1] == 0:
					return [pos.x for pos in self._internal[index[0]]]
				elif index[1] == 'y' or index[1] == 1:
					return [pos.y for pos in self._internal[index[0]]]
				else:
					raise ValueError(index[1])
			else:
				raise ValueError("Only 'int' and 'slice' can be used with 2D indexing")
		else:
			assert not isinstance(index, tuple)
		return super().__getitem__(index)
	
	def __setitem__(self, index: int, value: PositionLike | Position):
		if type(value) is not Position:
			value = Position(value[0], value[1])
		return super().__setitem__(index, value)
#endregion

	def __add__(self, other : PositionArray | Position | PositionLike):
		if type(other) is PositionArray:
			return PositionArray([ a + b for a,b in zip(self._internal, other._internal)])
		elif isinstance(other, Position) or isinstance(other, tuple|list|np.ndarray):
			return PositionArray( [a + other for a in self._internal] )
		else:
			raise ValueError(type(other))
	
	def __sub__(self, other : PositionArray | Position | PositionLike):
		if type(other) is PositionArray:
			return PositionArray([ a - b for a,b in zip(self._internal, other._internal)])
		elif isinstance(other, Position) or isinstance(other, tuple|list|np.ndarray):
			return PositionArray( [a - other for a in self._internal] )
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