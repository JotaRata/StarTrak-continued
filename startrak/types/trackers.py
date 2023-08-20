from typing import Any, List, Optional, Tuple
import numpy as np
from numpy.typing import NDArray
from startrak.types import Star, TrackingMethod
from startrak.types.alias import Position

class TriangleModel:
	__vertices: NDArray[np.uint16]
	__angles: List[float]
	def __init__(self) -> None:
		self.__vertices = np.empty((0, 2), dtype=np.uint16)
		self.__angles = list[float]()
	@property
	def centroids(self) -> List[List[float]]:
		size = self.__vertices.shape[0]
		return [np.mean(np.vstack( [self.__vertices[i, :],\
											self.__vertices[(i + 1)%size, :],\
											self.__vertices[(i + 2)%size, :]])\
							, axis= 0).tolist() 
					for i in range(0, size, 3)]
	@property
	def angles(self) -> List[float]:
		return self.__angles
	@property
	def vertices(self) -> List[Position]:
		return self.__vertices.tolist()
	@vertices.setter
	def vertices(self, val : List[Position]):
		self.__vertices = np.array(val)
		self.__angles = list[float]()
		for i in range(size:=len(val)):
			p1 = val[i]; p2 = val[(i + 1) % size]; p3 = val[(i + 2) % size]
			v1 = (p2[0] - p1[0], p2[1] - p1[1])
			v2 = (p3[0] - p1[0], p3[1] - p1[1])
			dot = np.dot(v1, v2)
			mag = np.sqrt(v1[0]**2 + v1[1]**2) * np.sqrt(v2[0]**2 + v2[1]**2)
			self.__angles.append(np.arccos(dot/mag))

# ------------------ Tracking methods ---------------

class SimpleTracker(TrackingMethod):
	track_size : int
	var_thresold : float
	_model : TriangleModel
	_star_values : List[float]

	def __init__(self, tracking_size : int, variation : float) -> None:
		self.track_size = tracking_size
		self.var_thresold = variation
		self._model = TriangleModel()
		self._star_values = list[float]()
	
	def setup_model(self, stars: List[Star], *args: Tuple):
		assert len(stars) >= 3, 'There should be at least three trackable stars'
		self._model.vertices = [star.position for star in stars]
		# todo: setup star brighness values
		
