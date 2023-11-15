import itertools
import math
from typing import List, Tuple, cast
import cv2
import numpy as np
from startrak.native import Star, StarDetector, Tracker, TrackingSolution
from startrak.native.alias import ImageLike
from startrak.types.detection import HoughCircles
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

class GlobalAlignment(Tracker):
	_detector : StarDetector

	def __init__(self, **detector_args) -> None:
		self._detector = HoughCircles(**detector_args)

	def setup_model(self, stars: List[Star]):
		coords = [star.position for star in stars]
		self._model = itertools.combinations(coords, 3)


	def _compare_triangles(self, trig1, trig2) -> bool:	#type:ignore
		def distance(point1, point2):
			return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
		def angle(side1, side2, side3):
			return math.degrees(math.acos((side1**2 + side2**2 - side3**2) / (2 * side1 * side2)))
		
		sides1 = [distance(trig1[i], trig1[(i+1)%3]) for i in range(3)]
		angles1 = [angle(sides1[i], sides1[(i+1)%3], sides1[(i+2)%3]) for i in range(3)]

		sides2 = [distance(trig2[i], trig2[(i+1)%3]) for i in range(3)]
		angles2 = [angle(sides2[i], sides2[(i+1)%3], sides2[(i+2)%3]) for i in range(3)]

		# Check if the ratios of corresponding sides and angles are equal
		side_ratios = [sides1[i] / sides2[i] for i in range(3)]
		angle_diffs = [abs(angles1[i] - angles2[i]) for i in range(3)]
		return all(0.95 <= ratio <= 1.05 for ratio in side_ratios) and all(diff < 1 for diff in angle_diffs)
	
	def track(self, image: ImageLike) -> TrackingSolution:
		detected_stars = self._detector.detect(image)
		coords = [star.position for star in detected_stars]
		triangles = itertools.combinations(coords, 3)

		# !warning: slow code
		matched = list[int]()
		for index, trig1 in enumerate(self._model):
			for trig2 in triangles:
				if self._compare_triangles(trig1, trig2):
					matched.append(index)
		
		return TrackingSolution.identity()