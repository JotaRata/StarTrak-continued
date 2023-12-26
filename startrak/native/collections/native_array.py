# compiled module
from __future__ import annotations
import numpy as np
from startrak.native.ext import STCollection
from numpy.typing import NDArray

class Array(STCollection[float]):
	def __add__(self, other: Array | float | int) -> Array:
		if isinstance(other, Array):
			return Array([ a + b for a,b in zip(self._internal, other._internal)])
		else:
			return Array( [a + other for a in self._internal] )
	
	def __radd__(self, other: Array | float | int) -> Array:
		return self.__add__(other)
	
	def __sub__(self, other: Array | float | int) -> Array:
		if isinstance(other, Array):
			return Array([ a - b for a,b in zip(self._internal, other._internal)])
		else:
			return Array( [a - other for a in self._internal] )
	
	def __mul__(self, other: Array | float | int) -> Array:
		if isinstance(other, Array):
			return Array([ a * b for a,b in zip(self._internal, other._internal)])
		else:
			return Array( [a * other for a in self._internal] )
	
	def __truediv__(self, other: Array | float | int) -> Array:
		if isinstance(other, Array):
			return Array( [ a / b for a,b in zip(self._internal, other._internal)])
		else:
			return Array( [a / other for a in self._internal] )
	
	def __array__(self, dtype=None) -> NDArray[np.float_]:
		return np.array(self._internal)