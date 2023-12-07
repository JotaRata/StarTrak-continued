# This file should only contain type aliases or generic type declarations.
from __future__ import annotations

from typing import Callable, List, TypeVar, Union
import numpy as np
from numpy.typing import NDArray

ValueType = Union[int, float, str, bool]
NumberLike = Union[np.uint, np.float_]
ImageLike = NDArray[NumberLike]

_DecoratorReturn = TypeVar('_DecoratorReturn')
Decorator = Callable[..., Callable[..., _DecoratorReturn]]

_IndexLike = int | bool 
_IndexLike_n =  np.int_ | np.bool_
MaskLike = List[_IndexLike] | NDArray[_IndexLike_n]