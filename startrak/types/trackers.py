from dataclasses import dataclass
from typing import Any, Generator, Iterator, List, Literal, Optional, Tuple, cast
import numpy as np
from numpy.typing import NDArray
from startrak.native import PhotometryBase, PhotometryResult, Star, Tracker, TrackingModel, TrackingSolution
from startrak.types import phot
from startrak.native.alias import ImageLike, Position, PositionArray
from startrak.types.phot import AperturePhot

# ------------------ Tracking methods ---------------

class SimpleTrackerModel(TrackingModel):
	coords : PositionArray
	phot : List[PhotometryResult]
	_phot_model : PhotometryBase

	def __init__(self, sample_image : ImageLike, stars : List[Star],
					phot_method : Literal['aperture'] | PhotometryBase = 'aperture') -> None:
		if phot_method == 'aperture':
			self._phot_model = AperturePhot(4, 2)	# todo: set by configuration
		elif isinstance(phot_method, PhotometryBase):
			self._phot_model = phot_method
		else:
			raise ValueError(phot_method)
		
		_coords : List[Position] = []
		self.phot = []

		# todo: use star brightness as an attribute
		for star in stars:
			_coords.append(star.position[::-1])
			phr = self._phot_model.evaluate(sample_image, star)
			self.phot.append(phr)
		self.coords = np.vstack(_coords)

	@property
	def count(self) -> int:
		return len(self.phot)

class SimpleTracker(Tracker[SimpleTrackerModel]):
	_size : int
	_factor : float
	_previous : PositionArray | None

	def __init__(self, tracking_size : int, sensitivity : float) -> None:
		self._size = tracking_size
		self._factor = sensitivity
		self._previous = None

	def track(self, _image : ImageLike):
		assert self._model is not None, "Tracking model hasn't been set"
		_reg : List[np.ndarray] = []
		_lost : List[int ]= []
		
		for i in range(self._model.count):
			row, col = self._model.coords[i]
			crop = _image[row - self._size : row + self._size,
								col - self._size : col + self._size]
			
			# background sigma clipping
			# image minus the background should equal the integrated flux
			# the candidate shouldn't be brighter than the current star
			mask = np.abs(crop - self._model.phot[i].backg) > 4 * self._model.phot[i].backg_sigma
			mask &= (crop - self._model.phot[i].backg) >=  self._model.phot[i].flux
			mask &= np.abs(crop - self._model.phot[i].flux) <  ( self._model.phot[i].flux_iqr * self._model.phot[i].flux / self._factor)
			
			indices = np.transpose(np.nonzero(mask))
			if len(indices) == 0:
				_lost.append(i)
				_reg.append(np.array([np.nan, np.nan]))
				continue
			
			_median = np.median(indices, axis= 0)
			_reg.append(_median - (self._size,) * 2 + self._model.coords[i])
		_current = np.vstack(_reg)

		dx = np.nanmean(_current[:, 0] - self._model.coords[:, 0])
		dy = np.nanmean(_current[:, 1] - self._model.coords[:, 1])

		#todo: if self._include_error:
		ex = np.nanstd(_current[:, 0] - self._model.coords[:, 0])
		ey = np.nanstd(_current[:, 1] - self._model.coords[:, 1])
		error = np.sqrt(ex**2 + ey**2)

		center : PositionArray = np.nanmean(self._model.coords, axis=0)
		c_previous = self._model.coords - center
		c_current = _current - center

		_dot = np.nansum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		_angle = np.nanmean(np.arctan2(_cross,  _dot))

		return TrackingSolution(cast(float, dx), cast(float, dy), _angle, error,  _lost)
