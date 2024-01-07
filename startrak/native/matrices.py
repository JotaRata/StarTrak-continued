# compiled module
from __future__ import annotations
import math
from typing import Any, NamedTuple, Tuple
import numpy as np

class Matrix2x2(NamedTuple):
	a: float
	b: float
	c: float
	d: float

	def __array__(self) -> np.ndarray[Any, Any]:  # Implementing the array protocol for compatibility
		return np.array([[self.a, self.b], [self.c, self.d]])

	def __mul__(self, other: Matrix2x2 | float | int) -> Matrix2x2: #type: ignore[override]
		if isinstance(other, (float, int)):
			return Matrix2x2(
				self.a * other,
				self.b * other,
				self.c * other,
				self.d * other
			)
		return Matrix2x2(
			self.a * other.a + self.b * other.c,
			self.a * other.b + self.b * other.d,
			self.c * other.a + self.d * other.c,
			self.c * other.b + self.d * other.d
		)
	
	def __add__(self, other : Matrix2x2):	#type: ignore[override]
		return Matrix2x2(
			self.a + other.a,
			self.b + other.b,
			self.c + other.c,
			self.d + other.d
		)

	@classmethod
	def identity(cls):
		return cls(1, 0, 0, 1)

	@property
	def transpose(self) -> Matrix2x2:
		return Matrix2x2(self.a, self.c, self.b, self.d)
	@property
	def determinant(self) -> float:
		return self.a * self.d - self.b * self.c
	@property
	def trace(self) -> float:
		return self.a + self.d
	@property
	def inverse(self) -> Matrix2x2:
		det = self.determinant
		if det == 0:
			raise ValueError("Matrix is not invertible.")
		factor = 1 / det
		return Matrix2x2(
			self.d * factor,
			-self.b * factor,
			-self.c * factor,
			self.a * factor )
	
	@property
	def eigenvalues(self) -> tuple[float, float]:
		tr = self.trace
		det = self.determinant
		lambda1 = 0.5 * (tr + math.sqrt(tr*tr - 4 * det))
		lambda2 = 0.5 * (tr - math.sqrt(tr*tr - 4 * det))
		return lambda1, lambda2
	@property
	def eigenvectors(self) -> Matrix2x2:
		lambda_1, lambda_2 = self.eigenvalues
		a = (lambda_1 - self.a) / self.b
		b = (lambda_2 - self.a) / self.b
		na = math.sqrt(1 + a*a)
		nb = math.sqrt(1 + b*b)
		
		v1 = (1. / na, a / na)
		v2 = (1. / nb, b / nb)
		return Matrix2x2(*v1, *v2).transpose
		
	
	def __repr__(self) -> str:
		return type(self).__name__ + f':\n[ {self.a:^8.4f} {self.b:^8.4f} ]\n[ {self.c:^8.4f} {self.d:^8.4f} ]'
	
	def __getitem__(self, index : Tuple[int , int ]) -> float: #type: ignore[override]
		i, j = index
		assert (0 <= i < 3) and (0 <= j < 3), 'Index out of range'
		return super().__getitem__( i * 2 + j)

from typing import NamedTuple, Any
import numpy as np

class Matrix3x3(NamedTuple):
	a: float
	b: float
	c: float
	d: float
	e: float
	f: float
	g: float
	h: float
	i: float

	def __array__(self) -> np.ndarray[Any, Any]:
		return np.array([[self.a, self.b, self.c], [self.d, self.e, self.f], [self.g, self.h, self.i]])

	def __mul__(self, other: Matrix3x3 | float | int) -> Matrix3x3:	#type: ignore[override]
		if isinstance(other, (float, int)):
			return Matrix3x3(
					self.a * other, self.b * other, self.c * other,
					self.d * other, self.e * other, self.f * other,
					self.g * other, self.h * other, self.i * other
			)
		return Matrix3x3(
			self.a * other.a + self.b * other.d + self.c * other.g,
			self.a * other.b + self.b * other.e + self.c * other.h,
			self.a * other.c + self.b * other.f + self.c * other.i,

			self.d * other.a + self.e * other.d + self.f * other.g,
			self.d * other.b + self.e * other.e + self.f * other.h,
			self.d * other.c + self.e * other.f + self.f * other.i,

			self.g * other.a + self.h * other.d + self.i * other.g,
			self.g * other.b + self.h * other.e + self.i * other.h,
			self.g * other.c + self.h * other.f + self.i * other.i
		)

	def __add__(self, other: Matrix3x3) -> Matrix3x3:	#type: ignore[override]
		return Matrix3x3(
			self.a + other.a, self.b + other.b, self.c + other.c,
			self.d + other.d, self.e + other.e, self.f + other.f,
			self.g + other.g, self.h + other.h, self.i + other.i
		)

	@classmethod
	def identity(cls):
		return cls(1, 0, 0, 0, 1, 0, 0, 0, 1)

	@property
	def transpose(self) -> Matrix3x3:
		return Matrix3x3(
			self.a, self.d, self.g,
			self.b, self.e, self.h,
			self.c, self.f, self.i
		)
	@property
	def determinant(self) -> float:
		return (
			self.a * (self.e * self.i - self.f * self.h) -
			self.b * (self.d * self.i - self.f * self.g) +
			self.c * (self.d * self.h - self.e * self.g)
		)
	@property
	def trace(self) -> float:
		return self.a + self.e + self.i

	@property
	def inverse(self) -> Matrix3x3:
		det = self.determinant
		if det == 0:
			raise ValueError("Matrix is not invertible.")
		factor = 1 / det
		return Matrix3x3(
			(self.e * self.i - self.f * self.h) * factor,
			-(self.b * self.i - self.c * self.h) * factor,
			(self.b * self.f - self.c * self.e) * factor,

			-(self.d * self.i - self.f * self.g) * factor,
			(self.a * self.i - self.c * self.g) * factor,
			-(self.a * self.f - self.c * self.d) * factor,

			(self.d * self.h - self.e * self.g) * factor,
			-(self.a * self.h - self.b * self.g) * factor,
			(self.a * self.e - self.b * self.d) * factor
		)

	def __repr__(self) -> str:
		return type(self).__name__ + f':\n[ {self.a:^8.4f} {self.b:^8.4f} {self.c:^8.4f} ]\n[ {self.d:^8.4f} {self.e:^8.4f} {self.f:^8.4f} ]\n[ {self.g:^8.4f} {self.h:^8.4f} {self.i:^8.4f} ]'
	
	def __getitem__(self, index : Tuple[int , int ]) -> float: #type: ignore[override]
		i, j = index
		return super().__getitem__( i * 3 + j)
