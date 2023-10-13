# nocompile
# This file should only contain type aliases or generic type declarations.

from typing import Any, Callable, Literal, Tuple, TypeVar, Union
import numpy as np
from numpy.typing import NDArray

ValueType = Union[int, float, str, bool]
NumberLike = Union[np.uint, np.float_]
ImageLike = NDArray[NumberLike]
Position = Tuple[int, int]
PositionArray = np.ndarray[ Tuple[int, Literal[2]], np.dtype[np.int_]]

_DecoratorReturn = TypeVar('_DecoratorReturn')
Decorator = Callable[..., Callable[..., _DecoratorReturn]]