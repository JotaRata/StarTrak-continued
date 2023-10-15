from dataclasses import dataclass
from typing import Any, Generator, Iterator, List, Literal, Optional, Tuple, cast
import cv2
import numpy as np
from numpy.typing import NDArray
from startrak.native import PhotometryBase, PhotometryResult, Star, Tracker, TrackingModel, TrackingSolution
from startrak.types import phot
from startrak.native.alias import ImageLike, Position, PositionArray
from startrak.types.phot import AperturePhot, _get_cropped

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

class SimpleTracker(Tracker):
	_size : int
	_factor : float

	def __init__(self, tracking_size : int, sensitivity : float,
					phot_method : Literal['aperture'] | PhotometryBase = 'aperture') -> None:
		self._size = tracking_size
		self._factor = sensitivity
		self._phot_model : PhotometryBase
		if phot_method == 'aperture':
			self._phot_model = AperturePhot(4, 2)	# todo: set by configuration
		elif isinstance(phot_method, PhotometryBase):
			self._phot_model = phot_method
		else:
			raise ValueError(phot_method)

	def setup_model(self, stars: List[Star]):
		_coords : List[Position] = []
		self.phot = []

		# todo: use star brightness as an attribute
		for star in stars:
			_coords.append(star.position[::-1])
			phr = self._phot_model.evaluate(sample_image, star)
			self.phot.append(phr)
		self.coords = np.vstack(_coords)

	def track(self, _image : ImageLike):
		assert self._model is not None, "Tracking model hasn't been set"
		_reg : List[np.ndarray] = []
		_lost : List[int ]= []
		downs : int | None = None; ksize : int = 3
		_f = downs / np.min(_image.shape) if downs is not None else 1
		img = cv2.resize(_image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
		img = cv2.medianBlur(img, 3)
		
		for i in range(self._model.count):
			row, col = self._model.coords[i]
			crop = _get_cropped(img, (col, row), 0, padding= self._size)
			
			# background sigma clipping
			# image minus the background should equal the integrated flux
			# the candidate shouldn't be brighter than the current star
			mask = np.abs(crop - self._model.phot[i].backg) > 2* self._model.phot[i].backg_sigma
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
		return TrackingSolution(_current, self._model.coords, _image.shape, _lost), _current