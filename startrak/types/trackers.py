from dataclasses import dataclass
from typing import Any, Generator, Iterator, List, Literal, Optional, Tuple, cast
import numpy as np
from numpy.typing import NDArray
from startrak.types import Star, Tracker, TrackingModel, TrackingSolution
from startrak.types.alias import ImageLike, PositionArray

# ------------------ Tracking methods ---------------

class SimpleTrackerModel(TrackingModel):
	positions : PositionArray
	values : List[float]

	def __init__(self, positions : PositionArray, values: List[float]) -> None:
		self.positions = positions
		self.values = values

class SimpleTracker(Tracker[SimpleTrackerModel]):
	_size : int
	_factor : float

	def __init__(self, tracking_size : int, variation : float) -> None:
		self._size = tracking_size
		self._factor = variation

	def track(self, _image : ImageLike):
		assert self._model is not None, "Tracking model hasn't been set"
		_reg : List[np.ndarray] = []
		_lost : List[int ]= []
		for i, (row, col) in enumerate(self._model.positions):
			crop = _image[row - self._size : row + self._size,
								col - self._size : col + self._size]
			mask = np.abs(self._model.values[i] - crop) < (self._model.values[i] * self._factor)
			indices = np.transpose(np.nonzero(mask))
			if len(indices) == 0:
				_lost.append(i)
				_reg.append(np.array([np.nan, np.nan]))
				continue
			
			_median = np.median(indices, axis= 0)
			_reg.append(_median - (self._size,) * 2 + self._model.positions[i])
		_current = np.vstack(_reg)

		dx = np.nanmean(_current[:, 0] - self._model.positions[:, 0])
		dy = np.nanmean(_current[:, 1] - self._model.positions[:, 1])

		#todo: if self._include_error:
		ex = np.nanstd(_current[:, 0] - self._model.positions[:, 0])
		ey = np.nanstd(_current[:, 1] - self._model.positions[:, 1])
		error = np.sqrt(ex**2 + ey**2)

		center : PositionArray = np.nanmean(self._model.positions, axis=0)
		c_previous = self._model.positions - center
		c_current = _current - center

		_dot = np.nansum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		_angle = np.nanmean(np.arctan2(_cross,  _dot))

		return TrackingSolution(cast(float, dx), cast(float, dy), _angle, error,  _lost)
