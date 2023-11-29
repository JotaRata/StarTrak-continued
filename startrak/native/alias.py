# This file should only contain type aliases or generic type declarations.
from __future__ import annotations

from typing import Callable, Collection, List, Literal, Tuple, TypeVar, Union
import numpy as np
from numpy.typing import NDArray
from startrak.native import Star
from startrak.native.collections import Position

ValueType = Union[int, float, str, bool]
NumberLike = Union[np.uint, np.float_]
ImageLike = NDArray[NumberLike]

PositionLike = Union[Tuple[int, int], List[int], NDArray[np.int_]]
StarList = List[Star]

_DecoratorReturn = TypeVar('_DecoratorReturn')
Decorator = Callable[..., Callable[..., _DecoratorReturn]]