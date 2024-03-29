# This file should only contain type aliases or generic type declarations.
from __future__ import annotations
from typing import Callable, Collection, List, Sequence, Tuple, TypeVar, Union
import numpy as np
from numpy.typing import NDArray as _NDArray

ValueType = Union[int, float, str, bool]
RealNumber = float | int
RealDType = Union[np.integer, np.floating, np.unsignedinteger]

_TReal = TypeVar('_TReal', bound= RealNumber)
_DReal = TypeVar('_DReal', np.integer, np.floating, np.unsignedinteger)

ImageLike = _NDArray[_DReal]
NDArray = _NDArray[RealDType]


_ArrayLike = Sequence[_TReal | Sequence[_TReal]] | NDArray
ArrayLike =  _ArrayLike[RealNumber]

_DecoratorReturn = TypeVar('_DecoratorReturn')
Decorator = Callable[..., Callable[..., _DecoratorReturn]]

_IndexLike = int | bool 
_IndexLike_n =  np.int_ | np.bool_
MaskLike = List[_IndexLike] | _NDArray[_IndexLike_n]