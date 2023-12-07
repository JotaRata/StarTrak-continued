from calendar import c
import itertools
import math
from typing import List, Literal, Tuple, cast
import cv2
import numpy as np
from startrak.native import PhotometryResult, Star, StarDetector, StarList, Tracker, TrackingIdentity, TrackingSolution
from startrak.native.alias import ImageLike, NDArray
from startrak.native import Position, PositionArray
from startrak.types.detection import HoughCircles
from startrak.types.phot import _get_cropped
from startrak.types import detection

class SimpleTracker(Tracker):
	_size : int
	_factor : float

	def __init__(self, tracking_size : int, sensitivity : float,
						rejection_sigma= 3, rejection_iter= 3) -> None:
		self._r_sigma = rejection_sigma
		self._r_iter = rejection_iter
		self._size = tracking_size
		self._factor = sensitivity

	def setup_model(self, stars: StarList):
		coords = PositionArray()
		phot = list[PhotometryResult]()
		for star in stars:
			if star.photometry:
				coords.append(star.position)
				phot.append(star.photometry)
		self._model_phot = phot
		self._model_count = len(phot)
		self._model_coords = coords
		self._model_coords.close()
		self._model_weights = np.array([p.flux for p in phot])
		self._model_weights = self._model_weights / np.mean(self._model_weights)

	def track(self, _image : ImageLike):
		current= PositionArray()
		lost= list[int]()
		img = cv2.resize(_image, None, fx=1, fy=1, interpolation=cv2.INTER_CUBIC)
		img = cv2.medianBlur(img, 3)
		
		for i in range(self._model_count): 
			crop = _get_cropped(img, self._model_coords[i], 0, padding= self._size)
			
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
				current.append([np.nan, np.nan])
				continue
			median_rc = np.median(indices, axis= 0)[::-1]
			current.append(median_rc - (self._size,) * 2 + self._model_coords[i])
		
		delta_pos = current - self._model_coords
		
		center = _image.shape[1]/2, _image.shape[0]/2
		c_previous = self._model_coords - center
		c_current = current - center

		dot = np.nansum(np.multiply(c_previous, c_current), axis= 1)
		cross = np.cross(c_previous, c_current)
		da = np.arctan2(cross,  dot)

		return TrackingSolution(delta_pos= delta_pos, 
										delta_angle= da, 
										image_size= _image.shape, 
										lost_indices= lost,
										weights= self._model_weights,
										rejection_sigma= self._r_sigma,
										rejection_iter= self._r_iter)
	
_Method = Literal['hough', 'hough_adaptive', 'hough_threshold']
class GlobalAlignmentTracker(Tracker):
	_detector : StarDetector
	_method : str
	def __init__(self, detection_method : _Method | StarDetector = 'hough',
							congruence_method: Literal['sss', 'sas'] = 'sss',
							congruence_criterium : float = 0.05,
							area_weight : bool = True,
							rejection_sigma= 3, rejection_iter= 3,  **detector_args) -> None:
		self._r_sigma = rejection_sigma
		self._r_iter = rejection_iter
		self._c = congruence_criterium
		self._method = congruence_method
		self._use_w = area_weight
		if detection_method == 'hough':
			self._detector = detection.HoughCircles(**detector_args)
		elif detection_method == 'hough_adaptive':
			self._detector = detection.AdaptiveHoughCircles(**detector_args)
		elif detection_method == 'hough_threshold':
			self._detector = detection.ThresholdHoughCircles(**detector_args)
		elif isinstance(detection_method, StarDetector):
			self._detector = detection_method
		else:
			raise ValueError(detection_method)

	def _neighbors(self, pos_array : PositionArray, k= 2) -> NDArray[np.int_]:
		x = pos_array[:, 0]
		y = pos_array[:, 1]
		dist = np.subtract.outer(x, x)**2 + np.subtract.outer(y, y)**2
		return np.argpartition(dist, k+1, axis=1)[:, :k+1]
	
	def _compare_sss(self, trig1, trig2) -> bool:
		a1 =  (trig1[0][0] - trig1[1][0])**2 + (trig1[0][1] - trig1[1][1])**2
		b1 =  (trig1[0][0] - trig1[2][0])**2 + (trig1[0][1] - trig1[2][1])**2
		c1 =  (trig1[1][0] - trig1[2][0])**2 + (trig1[1][1] - trig1[2][1])**2
		a2 =  (trig2[0][0] - trig2[1][0])**2 + (trig2[0][1] - trig2[1][1])**2
		b2 =  (trig2[0][0] - trig2[2][0])**2 + (trig2[0][1] - trig2[2][1])**2
		c2 =  (trig2[1][0] - trig2[2][0])**2 + (trig2[1][1] - trig2[2][1])**2

		return (	((1-self._c) <= a1/a2 < 1+self._c) and
					((1-self._c) <= b1/b2 < 1+self._c) and
					((1-self._c) <= c1/c2 < 1+self._c) )
	def _compare_sas(self, trig1, trig2) -> bool:
		a1 = (trig1[0][0] - trig1[1][0])**2 + (trig1[0][1] - trig1[1][1])**2
		b1 = (trig1[0][0] - trig1[2][0])**2 + (trig1[0][1] - trig1[2][1])**2
		c1 = (trig1[1][0] - trig1[2][0])**2 + (trig1[1][1] - trig1[2][1])**2
		angle1 = np.arccos((b1 + c1 - a1) / (2 * np.sqrt(b1 * c1)))
		a2 = (trig2[0][0] - trig2[1][0])**2 + (trig2[0][1] - trig2[1][1])**2
		b2 = (trig2[0][0] - trig2[2][0])**2 + (trig2[0][1] - trig2[2][1])**2
		c2 = (trig2[1][0] - trig2[2][0])**2 + (trig2[1][1] - trig2[2][1])**2
		angle2 = np.arccos((b2 + c2 - a2) / (2 * np.sqrt(b2 * c2)))
		return (	((1-self._c) <= a1/a2 < 1+self._c) and
					((1-self._c) <= b1/b2 < 1+self._c) and
					((1-self._c) <= angle1/angle2 < 1+self._c) )
	def _calc_area(self, trig) -> float:
		a = math.sqrt((trig[0, 0] - trig[1, 0])**2 + (trig[0, 1] - trig[1, 1])**2)
		b = math.sqrt((trig[0, 0] - trig[2, 0])**2 + (trig[0, 1] - trig[2, 1])**2)
		c = math.sqrt((trig[1, 0] - trig[2, 0])**2 + (trig[1, 1] - trig[2, 1])**2)
		s = (a+b+c) / 2
		return np.sqrt(s*(s-a)*(s-b)*(s-c))

	def setup_model(self, stars: StarList):
		if len(stars) <= 3:
			raise RuntimeError(f'Model of {type(self).__name__} requires more than 3 stars to set up')
		
		coords = stars.positions
		self._indices = self._neighbors(coords)
		self._model = list[PositionArray]()
		
		idx : NDArray[np.int_]
		for idx in self._indices:
			coord = coords[idx]
			coord.close()
			self._model.append(coord)

		if self._use_w:
			self._areas = np.array([self._calc_area(trig) for trig in self._model])

	def track(self, image: ImageLike) -> TrackingSolution:
		''' 
			Based on "Efficient k-Nearest Neighbors (k-NN) Solutions with NumPy" by Peng Qian (2023)
			https://www.dataleadsfuture.com/efficient-k-nearest-neighbors-k-nn-solutions-with-numpy/
		'''
		detected_stars = self._detector.detect(image)
		if len(detected_stars) <= 3:
			print('Less than 3 stars were detected for this image')
			return TrackingIdentity()
		method = self._compare_sas if self._method == 'sas' else self._compare_sss
		
		coords = detected_stars.positions
		indices = self._neighbors(coords)
		triangles : List[PositionArray] = [coords[idx] for idx in indices]
		
		# !warning: slow code
		matched = list[Tuple[int, int]]()
		for i, trig1 in enumerate(self._model):
			for j, trig2 in enumerate(triangles):
				if method(trig1, trig2):
					matched.append((i, j))
					break
		if len(matched) == 0:
			print('No triangles were matched for this image')
			return TrackingIdentity()
		
		reference = PositionArray()
		current = PositionArray()
		_areas = list[float]()

		for model_idx, current_idx in matched:
			model = self._model[model_idx]
			triangle = triangles[current_idx]
			
			reference.extend(model)
			current.extend(triangle)
			if self._use_w:
				_areas.append(self._areas[model_idx])

		center = image.shape[1]/2, image.shape[0]/2
		
		dot = np.nansum(np.multiply((reference - center), (current - center)), axis= 1)
		cross = np.cross((reference - center), (current - center))
		
		delta_pos = current - reference
		delta_rot = np.arctan2(cross,  dot)

		if self._use_w:
			weight_array = np.repeat(_areas, 3)
		else:
			weight_array = None

		print(f'Matched {len(matched)} of {len(triangles)} triangles')
		return TrackingSolution(delta_pos= delta_pos,
										delta_angle= delta_rot,
										image_size= image.shape,
										weights= weight_array,
										rejection_iter= self._r_iter,
										rejection_sigma= self._r_sigma)