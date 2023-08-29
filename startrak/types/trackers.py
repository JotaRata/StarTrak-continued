from typing import Any, Iterator, List, Literal, Optional, Tuple, cast
import numpy as np
from numpy.typing import NDArray
from startrak.types import Star, Tracker, TrackingModel
from startrak.types.alias import ImageLike, PositionArray

# ------------------ Tracking methods ---------------

class SimpleTracker(Tracker[PositionArray]):
	_size : int
	_factor : float
	_values : List[float]

	def __init__(self, tracking_size : int, variation : float) -> None:
		self._size = tracking_size
		self._factor = variation
		self._values = list[float]()
	
	def setup_model(self, stars: List[Star], *args: Tuple):
		assert len(stars) >= 3, 'There should be at least three trackable stars'
		self._model = np.vstack([star.position for star in stars])
		# todo: setup star brighness values

	def track(self, images: Iterator[ImageLike]) -> TrackingModel:
		assert self._model is not None, "Tracking model hasn't been set"
		if self._previous is None:
			self._previous = self._model.copy()
		
		_image = next(images)
		_positions = []
		for i, (col, row)  in enumerate(self._previous):
			crop = _image[row - self._size : row + self._size,
								col - self._size : col + self._size]
			mask = np.abs(self._values[i] - crop) < (self._values[i] * self._factor)
			indices = np.nonzero(mask)
			_median = np.median(indices, axis= 0)
			_positions.append(_median)

		self._current = np.vstack(_positions)

		dx = np.mean(self._current[:, 0] - self._previous[:, 0])
		dy = np.mean(self._current[:, 1] - self._previous[:, 1])

		center : PositionArray = np.mean(self._previous, axis=0)
		c_previous = self._previous - center
		c_current = self._current - center

		_dot = np.sum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		_angle = np.mean(np.arctan2(_cross,  _dot))

		self._previous = self._current
		return TrackingModel(cast(float, dx), cast(float, dy), _angle)
