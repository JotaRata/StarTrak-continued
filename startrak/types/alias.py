# nocompile
# This file should only contain type aliases or generic type declarations.

from typing import Any, Union
import numpy as np

_ValueType = Union[int, float, str, bool]
_NumberLike = Union[np.uint, np.float_]
_ImageLike = np.ndarray[Any, np.dtype[_NumberLike]]