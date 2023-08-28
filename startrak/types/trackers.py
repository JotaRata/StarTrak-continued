from typing import Any, Iterator, List, Literal, Optional, Tuple
import numpy as np
from numpy.typing import NDArray
from startrak.types import Star, Tracker
from startrak.types.alias import ImageLike, PositionArray

# ------------------ Tracking methods ---------------

class SimpleTracker(Tracker[PositionArray]):
	track_size : int
	var_thresold : float
	_star_values : List[float]

	def __init__(self, tracking_size : int, variation : float) -> None:
		self.track_size = tracking_size
		self.var_thresold = variation
		self._star_values = list[float]()
	
	def setup_model(self, stars: List[Star], *args: Tuple):
		assert len(stars) >= 3, 'There should be at least three trackable stars'
		self._model = np.vstack([star.position for star in stars])
		# todo: setup star brighness values

	def track(self, images: Iterator[ImageLike]):
		assert self._model is not None, "Tracking model hasn't been set"
		if self._current is None:
			self._current = self._model.copy()
		if self._previous is None:
			return
		dx = np.mean(self._current[:, 0] - self._previous[:, 0])
		dy = np.mean(self._current[:, 1] - self._previous[:, 1])

		center : PositionArray = np.mean(self._previous, axis=0)
		c_previous = self._previous - center
		c_current = self._current - center

		_dot = np.sum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		_angle = np.mean(np.arctan2(_cross,  _dot))

		self._previous = self._current
