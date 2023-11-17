from calendar import c
import itertools
import math
from typing import List, Literal, Tuple, cast
import cv2
import numpy as np
from startrak.native import Star, StarDetector, Tracker, TrackingIdentity, TrackingSolution
from startrak.native.alias import ImageLike
from startrak.types.detection import HoughCircles
from startrak.types.phot import _get_cropped
from startrak.types import detection

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

		diff = current - self._model_coords
		
		_center = tuple(np.nanmean(current, axis=0).tolist())
		c_previous = self._model_coords - _center
		c_current = current - _center

		_dot = np.nansum(c_previous * c_current, axis= 1)
		_cross = np.cross(c_previous, c_current)
		da = np.arctan2(_cross,  _dot)

		return TrackingSolution(delta_pos= diff, 
										delta_angle= da, 
										image_size= _image.shape, 
										lost_indices= lost)
	
_Method = Literal['hough', 'hough_adaptive', 'hough_threshold']
class GlobalAlignmentTracker(Tracker):
	_detector : StarDetector
	_method : str
	_r_sigma : int
	_r_iter : int
	_c : float
	
	def __init__(self, detection_method : _Method | StarDetector = 'hough',
							congruence_method: Literal['sss', 'sas'] = 'sss',
							congruence_criterium : float = 0.05,
							rejection_sigma= 3, rejection_iter= 3,  **detector_args) -> None:
		self._r_sigma = rejection_sigma
		self._r_iter = rejection_iter
		self._c = congruence_criterium
		self._method = congruence_method
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

	def _neighbors(self, pos_array):
		n = len(pos_array); k = 2
		
		a = pos_array.reshape(n, 1)
		b = pos_array.reshape(1, n)
		dist = (a['x'] - b['x'])**2 + (a['y'] - b['y'])**2
		return np.argpartition(dist, k+1, axis=1)[:, :k+1]

	def setup_model(self, stars: List[Star]):
		if len(stars) <= 3:
			raise RuntimeError(f'Model of {type(self).__name__} requires more rhan 3 stars to set up')
		# todo: include this in Position class
		dt = np.dtype([('x', 'int'), ('y', 'int')])
		coords = np.array([star.position[::-1] for star in stars], dtype= dt)
		
		self._indices = self._neighbors(coords)
		self._model = coords[self._indices]

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

	def track(self, image: ImageLike) -> TrackingSolution:
		''' 
			Based on "Efficient k-Nearest Neighbors (k-NN) Solutions with NumPy" by Peng Qian (2023)
			https://www.dataleadsfuture.com/efficient-k-nearest-neighbors-k-nn-solutions-with-numpy/
		'''
		detected_stars = self._detector.detect(image)
		if len(detected_stars) <= 3:
			print('Less than 3 stars were detected for this image')
			return TrackingIdentity()
		dt = np.dtype([('x', 'int'), ('y', 'int')])
		coords = np.array([star.position[::-1] for star in detected_stars], dtype= dt)
		triangles = self._neighbors(coords)
		TPos = Tuple[float, float]
		# !warning: slow code
		matched = list[Tuple[int, int]]()
		method = self._compare_sas if self._method == 'sas' else self._compare_sss
		for i, trig1 in enumerate(self._model):
			for j, indices in enumerate(triangles):
				if method(trig1, coords[indices]):
					matched.append((i, j))
					break
		if len(matched) == 0:
			print('No triangles were matched for this image')
			return TrackingIdentity()
		delta_pos = []
		delta_rot = []
		_centroids = []
		for model_idx, current_idx in matched:
			model = self._model.view((int, len(self._model.dtype.names)))[model_idx]
			triangle = coords.view((int, len(coords.dtype.names)))[triangles[current_idx]]#type:ignore

			centroid1 = np.mean(model, axis= 0)
			centroid2 = np.mean(triangle, axis= 0)

			_dot = np.nansum((model - centroid1) * (triangle - centroid2), axis= 1)
			_cross = np.cross((model - centroid1), (triangle - centroid2))
			da = np.nanmean(np.arctan2(_cross,  _dot))

			delta_pos.append(centroid2 - centroid1)
			delta_rot.append(da)
			_centroids.append(centroid2)
			
		pos_array = np.repeat(np.vstack(delta_pos), 3, axis=0)
		rot_array = np.repeat(delta_rot, 3)

		print(f'Matched {len(matched)} of {len(triangles)} triangles')
		return TrackingSolution(delta_pos= pos_array,
										delta_angle= rot_array,
										image_size= image.shape,
										rejection_iter= self._r_iter,
										rejection_sigma= self._r_sigma)