from calendar import c
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

	def _neighbors(self, pos_array):
		n = len(pos_array); k = 2
		
		a = pos_array.reshape(n, 1)
		b = pos_array.reshape(1, n)
		dist = (a['x'] - b['x'])**2 + (a['y'] - b['y'])**2
		return np.argpartition(dist, k+1, axis=1)[:, :k+1]

	def setup_model(self, stars: List[Star]):
		# todo: include this in Position class
		dt = np.dtype([('x', 'int'), ('y', 'int')])
		coords = np.array([star.position[::-1] for star in stars], dtype= dt)
		
		self._indices = self._neighbors(coords)
		self._model = coords[self._indices]

	def _compare(self, trig1, trig2) -> bool:
		a1 =  (trig1[0][0] - trig1[1][0])**2 + (trig1[0][1] - trig1[1][1])**2
		b1 =  (trig1[0][0] - trig1[2][0])**2 + (trig1[0][1] - trig1[2][1])**2
		if a1 == 0 or b1 == 0: return False
		c1 =  (trig1[1][0] - trig1[2][0])**2 + (trig1[1][1] - trig1[2][1])**2
		ang1 = np.arccos((a1 + b1 - c1) / (2 * a1 * b1))

		a2 =  (trig2[0][0] - trig2[1][0])**2 + (trig2[0][1] - trig2[1][1])**2
		b2 =  (trig2[0][0] - trig2[2][0])**2 + (trig2[0][1] - trig2[2][1])**2
		if a2 == 0 or b2 == 0: return False
		c2 =  (trig2[1][0] - trig2[2][0])**2 + (trig2[1][1] - trig2[2][1])**2
		ang2 = np.arccos((a2 + b2 - c2) / (2 * a2 * b2))
		return ((0.95 <= a1/a2 < 1.05) and (0.95 <= b1/b2 < 1.05)) and (np.abs(ang2 - ang1) < 0.05)

	def track(self, image: ImageLike) -> TrackingSolution:
		''' 
			Based on "Efficient k-Nearest Neighbors (k-NN) Solutions with NumPy" by Peng Qian (2023)
			https://www.dataleadsfuture.com/efficient-k-nearest-neighbors-k-nn-solutions-with-numpy/
		'''
		detected_stars = self._detector.detect(image)
		dt = np.dtype([('x', 'int'), ('y', 'int')])
		coords = np.array([star.position[::-1] for star in detected_stars], dtype= dt)
		triangles = self._neighbors(coords)
		TPos = Tuple[float, float]
		# !warning: slow code
		matched = list[Tuple[int, int]]()
		for i, trig1 in enumerate(self._model):
			for j, indices in enumerate(triangles):
				if self._compare(trig1, coords[indices]):
					matched.append((i, j))
					break
		print(f'Matched {len(matched)} of {len(triangles)} triangles by SAS')
		if len(matched) <= 1:
			return TrackingSolution.identity()
		delta_pos = []
		delta_rot = []
		_centroids = []
		for model_idx, current_idx in matched:
			model = self._model.view((int, len(self._model.dtype.names)))[model_idx]
			triangle = coords.view((int, len(coords.dtype.names)))[triangles[current_idx]]

			centroid1 = np.mean(model, axis= 0)
			centroid2 = np.mean(triangle, axis= 0)

			_dot = np.nansum((model - centroid1) * (triangle - centroid2), axis= 1)
			_cross = np.cross((model - centroid1), (triangle - centroid2))
			da = np.nanmean(np.arctan2(_cross,  _dot))

			delta_pos.append(centroid2 - centroid1)
			delta_rot.append(da)
			_centroids.append(centroid2)
		
		ex, ey = np.nanstd(delta_pos, axis= 0)
		error = np.sqrt(ex**2 + ey**2)
		
		dpos = tuple(np.nanmean(delta_pos, axis= 0).tolist())
		dangle = np.nanmean(delta_rot)
		center = tuple(np.nanmean(_centroids, axis= 0).tolist())
		return TrackingSolution(delta_pos= cast(TPos, dpos),
										delta_angle= cast(float, dangle),
										error= error,
										origin= cast(TPos, center))