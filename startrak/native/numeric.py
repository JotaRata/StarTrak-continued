# compiled module
from __future__ import annotations
import math
from typing import Collection, Iterable, List, Literal, Self, Sized, Tuple, TypeVar, cast, overload

import numpy as np
from startrak.native import Position
from startrak.native.alias import MaskLike
from startrak.native.ext import STCollection
from numpy.typing import NDArray, ArrayLike


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
		
@overload
def average(values : Collection[float] | Array, weights : Collection[float] | None) -> float: ...
@overload
def average(values : Collection[Position], weights : Collection[float] | None) -> Position: ...
def average(values : Collection[float | Position] | Array, weights : Collection[float] | None = None) -> float | Position:
	if weights is not None and (s := sum(weights)) != 0:
		assert len(values) == len(weights)
		return sum([n * w for n, w in zip(values, weights)]) / s
	else:
		return sum(values) / len(values)


def variance(values : Collection[float] | Array, weights : Collection[float] | None = None) -> float:
	avg = average(values, weights)
	if weights is not None and (s := sum(weights)) != 0:
		assert len(values) == len(weights)
		return sum([ w * (n - avg) ** 2 for n, w in zip(values, weights)]) / s
	else:
		return sum((n -  avg) * (n -  avg) for n in values) / len(values)

def stdev(values : Collection[float] | Array, weights : Collection[float] | None = None) -> float:
	return math.sqrt(variance(values, weights))