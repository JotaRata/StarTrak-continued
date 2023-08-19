# nocompile
# This file should only contain type aliases or generic type declarations.

from typing import Any, Callable, TypeVar, Union
import numpy as np
from numpy.typing import NDArray

ValueType = Union[int, float, str, bool]
NumberLike = Union[np.uint, np.float_]
ImageLike = NDArray[NumberLike]

_DecoratorReturn = TypeVar('_DecoratorReturn')
Decorator = Callable[..., Callable[..., _DecoratorReturn]]