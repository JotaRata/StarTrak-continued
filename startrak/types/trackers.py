from typing import List, Tuple, cast
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
		_reg= []
		lost= []
		TPos = Tuple[float, float]
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
				lost.append(i)
				_reg.append(np.array([np.nan, np.nan]))
				continue
			
			_median = np.median(indices, axis= 0)
			_reg.append(_median - (self._size,) * 2 + self._model_coords[i])
		current = np.vstack(_reg)

		_diff = current - self._model_coords
		errors = _diff - np.nanmean(_diff, axis= 0)

		for i, (exx, eyy) in enumerate(errors):
			if (_err:= exx**2 + eyy**2) > max(2 * np.nanmean(errors**2), 1):
				print(f'Star {i} is deviating from the solution ({_err:.1f} px)')
				lost.append(i)
		bad_mask = [index not in lost for index in range(self._model_count)]

		_center = tuple(np.nanmean(current[bad_mask], axis=0).tolist())
		c_previous = self._model_coords[bad_mask] - _center
		c_current = current[bad_mask] - _center

		_dot = np.nansum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		da = np.nanmean(np.arctan2(_cross,  _dot))

		ex, ey = np.nanstd(_diff[bad_mask], axis= 0)
		error = np.sqrt(ex**2 + ey**2)
		dpos = tuple(np.nanmean(_diff[bad_mask], axis= 0).tolist())
		return TrackingSolution(delta_pos= cast(TPos, dpos), 
										delta_angle= float(da), 
										error= float(error), 
										origin= cast(TPos, _center), 
										lost_indices= lost)
	
