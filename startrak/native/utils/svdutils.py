# compiled module
from __future__ import annotations
import math

from startrak.native.collections.position import PositionArray
from startrak.native.matrices import Matrix2x2
from startrak.native.numeric import average

def outer(a: PositionArray, b: PositionArray) -> Matrix2x2:
	assert len(a) == len(b), "Input arrays must have the same length."
	return Matrix2x2(
		sum(pos_a.x * pos_b.x for pos_a, pos_b in zip(a, b)),
		sum(pos_a.x * pos_b.y for pos_a, pos_b in zip(a, b)),
		sum(pos_a.y * pos_b.x for pos_a, pos_b in zip(a, b)),
		sum(pos_a.y * pos_b.y for pos_a, pos_b in zip(a, b)) )

def covariance(a : PositionArray):
	mean_x, mean_y = average(a)
	cov_xx = average( [(pos.x - mean_x) * (pos.x - mean_x) for pos in a] )
	cov_yy = average( [(pos.y - mean_y) * (pos.y - mean_y) for pos in a] )
	cov_xy = average( [(pos.x - mean_x) * (pos.y - mean_y) for pos in a] )
	return Matrix2x2(cov_xx, cov_xy, cov_xy, cov_yy)



def SVD(A: Matrix2x2) :
	ata = A.transpose * A
	aat = A * A.transpose

	v_matrix = ata.eigenvectors
	u_matrix = aat.eigenvectors

	# Singular values are square roots of eigenvalues
	singular_values = tuple(math.sqrt(lambda_i) for lambda_i in ata.eigenvalues)

	return singular_values, u_matrix, v_matrix

