# compiled module
from __future__ import annotations
import math
from typing import Collection, overload
from startrak.native.collections.position import Position

@overload
def average(values : Collection[float], weights : Collection[float] | None = None) -> float: ...
@overload
def average(values : Collection[Position], weights : Collection[float] | None = None) -> Position: ...
def average(values : Collection[float | Position], weights : Collection[float] | None = None) -> float | Position:
	if weights is not None and (s := sum(weights)) != 0:
		assert len(values) == len(weights)
		return sum([n * w for n, w in zip(values, weights)]) / s
	else:
		return sum(values) / len(values)


def variance(values : Collection[float], weights : Collection[float] | None = None) -> float:
	avg = average(values, weights)
	if weights is not None and (s := sum(weights)) != 0:
		assert len(values) == len(weights)
		return sum([ w * (n - avg) ** 2 for n, w in zip(values, weights)]) / s
	else:
		return sum((n -  avg) * (n -  avg) for n in values) / len(values)

def stdev(values : Collection[float], weights : Collection[float] | None = None) -> float:
	return math.sqrt(variance(values, weights))