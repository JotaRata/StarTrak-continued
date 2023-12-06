# compiled module
from abc import abstractproperty
from typing import ClassVar, Generic, Iterable, Iterator, List, Self, TypeVar, overload
import numpy as np
from startrak.native.alias import MaskLike
from mypy_extensions import mypyc_attr, trait

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

TList = TypeVar('TList')
class STCollection(STObject, Generic[TList]):
	_internal : List[TList]
	_closed : bool

	def __init__(self, values : Iterable[TList] | None = None ):
		self._closed = False
		if values is None:
			self._internal = list[TList]()
		else:
			self._internal = list[TList](values)
		self.__post_init__()

	def __post_init__(self):
		pass
	
	@property
	def is_closed(self) -> bool:
		return getattr(self, '_closed', False)
	
	def close(self):
		self._closed = True

	def __on_change__(self):
		if self.is_closed:
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
	def __getitem__(self, index :  slice | MaskLike) -> Self: ...

	def __getitem__(self, index : int | slice | MaskLike) -> Self | TList:
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
		self.__on_change__()
		return self._internal.__setitem__(index, value)
	
	def append(self, value: TList): 
		self.__on_change__()
		self._internal.append(value)
	
	def extend(self, values: Self | Iterable[TList]): 
		self.__on_change__()
		return self._internal.extend(values)
	
	def insert(self, index: int, value: TList): 
		self.__on_change__()
		self._internal.insert(index, value)
	
	def remove(self, value: TList): 
		self.__on_change__()
		self._internal.remove(value)
	
	def pop(self, index: int) -> TList: 
		self.__on_change__()
		return self._internal.pop(index)
	
	def clear(self): 
		self.__on_change__()
		self._internal.clear()
	
	def reverse(self): 
		self.__on_change__()
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