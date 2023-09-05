from typing import Any, Generator, Iterator, List, Literal, Optional, Tuple, cast
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
	
	def setup_model(self, stars: List[Star], *args):
		assert len(stars) >= 3, 'There should be at least three trackable stars'
		self._model = np.vstack([star.position[::-1] for star in stars])
		# todo: setup star brighness values

	def track(self, _image : ImageLike):
		assert self._model is not None, "Tracking model hasn't been set"
		if self._previous is None:
			self._previous = self._model.copy()
		
		if self._values is None or len(self._values) == 0:
			self._values = _image[*self._previous.T].tolist()
		_positions = []
		for i, (row, col) in enumerate(self._previous):
			crop = _image[row - self._size : row + self._size,
								col - self._size : col + self._size]
			mask = np.abs(self._values[i] - crop) < (self._values[i] * self._factor)
			indices = np.transpose(np.nonzero(mask))
			if len(indices) == 0:
				_positions.append(self._previous[i])
				continue
			
			_median = np.median(indices, axis= 0)
			_positions.append(_median - (self._size,) * 2 + self._previous[i])

		self._current = np.vstack(_positions)

		dx = np.nanmean(self._current[:, 0] - self._previous[:, 0])
		dy = np.nanmean(self._current[:, 1] - self._previous[:, 1])

		center : PositionArray = np.nanmean(self._previous, axis=0)
		c_previous = self._previous - center
		c_current = self._current - center

		_dot = np.nansum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		_angle = np.nanmean(np.arctan2(_cross,  _dot))

		self._previous = self._current.astype(int)
		return TrackingModel(cast(float, dx), cast(float, dy), _angle)
