from typing import List
import cv2
import numpy as np
from startrak.native import Star, Tracker, TrackingSolution
from startrak.native.alias import ImageLike
from startrak.types.phot import _get_cropped

class SimpleTracker(Tracker):
	_size : int
	_factor : float

	def __init__(self, tracking_size : int, sensitivity : float) -> None:
		self._size = tracking_size
		self._factor = sensitivity

	def setup_model(self, stars: List[Star]):
		coords = []
		phot = []
		for star in stars:
			if star.photometry:
				coords.append(star.position[::-1])
				phot.append(star.photometry)
		self._model_phot = phot
		self._model_count = len(phot)
		self._model_coords = np.vstack(coords)

	def track(self, _image : ImageLike):
		_reg : List[np.ndarray] = []
		_lost : List[int ]= []
		img = cv2.resize(_image, None, fx=1, fy=1, interpolation=cv2.INTER_CUBIC)
		img = cv2.medianBlur(img, 3)
		
		for i in range(self._model_count):
			row, col = self._model_coords[i]
			crop = _get_cropped(img, (col, row), 0, padding= self._size)
			
			# background sigma clipping
			# image minus the background should equal the integrated flux
			# the candidate shouldn't be brighter than the current star
			phot = self._model_phot[i]
			mask = np.abs(crop - phot.backg) > 2* phot.backg_sigma
			mask &= (crop - phot.backg) >=  phot.flux
			mask &= np.abs(crop - phot.flux) <  ( phot.flux_iqr * phot.flux / self._factor)
			
			indices = np.transpose(np.nonzero(mask))
			if len(indices) == 0:
				_lost.append(i)
				_reg.append(np.array([np.nan, np.nan]))
				continue
			
			_median = np.median(indices, axis= 0)
			_reg.append(_median - (self._size,) * 2 + self._model_coords[i])
		_current = np.vstack(_reg)
		return TrackingSolution(_current, self._model_coords, _image.shape, _lost), _current