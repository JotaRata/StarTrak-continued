from typing import List, Literal, Tuple
import numpy as np
from startrak.native.classes import TrackingSolution
from startrak.native.numeric import average

from startrak.native.utils.geomutils import *
from startrak.native import Array, PhotometryResult, StarDetector, StarList, Tracker, TrackingSolution
from startrak.native.alias import ImageLike
from startrak.native import PositionArray
from startrak.types.phot import _get_cropped
from startrak.types import detection

class PhotometryTracker(Tracker):
	def __init__(self, tracking_size : int, tracking_steps : int = 1, size_mul : float = 0.5,
						rejection_sigma= 3, rejection_iter= 3) -> None:
		self._steps = tracking_steps
		self._sizemul = size_mul
		self._r_sigma = rejection_sigma
		self._r_iter = rejection_iter
		self._size = tracking_size

	def setup_model(self, stars: StarList, weights : Tuple[float, ...] | None= None, **kwargs):
		
		if weights and type(weights) is tuple:
			if len(weights) != len(stars):
				raise ValueError('Weights size must be equal to star list size')
			self._model_weights = weights
		else:
			self._model_weights = (1, ) * len(stars)
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

	def _track(self, _image : ImageLike, start_coords : PositionArray,
					crop_size : int ):
		current = PositionArray()
		lost = list[int]()
		for i in range(self._model_count): 
			if i in lost:
				pass
			crop = _get_cropped(_image, start_coords[i], 0, padding= crop_size)
			phot = self._model_phot[i]
			bkg = np.nanmean((np.nanmean(crop[-4:, :]), np.nanmean(crop[:, -4:]), np.nanmean(crop[:4, :]), np.nanmean(crop[:, :4])))
			
			try:	
				mask = (crop - bkg) > phot.background.sigma * (1 + phot.snr * 2)
				mask &= (crop - bkg) > phot.flux.sigma * (1 + phot.snr) / 2
				mask &= ((crop - bkg) - phot.flux.max) <  phot.flux.sigma
				mask &= ~np.isnan(crop)

				indices = np.transpose(np.nonzero(mask))
				if len(indices) == 0: raise IndexError()
				_w = np.clip(crop[indices[:, 0], indices[:, 1]] - bkg, 0, phot.flux.max) / phot.flux
				_w[np.isnan(_w)] = 0
				avg = np.average(indices, weights= _w ** 2, axis= 0)[::-1]
			except:	#raises ZeroDivisionError and IndexError
				lost.append(i)
				current.append([0, 0])
				continue
			current.append(avg - (crop_size,) * 2 + start_coords[i])
		
		delta_pos = current - start_coords
		return delta_pos, lost
	
	def track(self, image: ImageLike) -> TrackingSolution:
		current = self._model_coords.copy()
		lost = list[int]()
		_size = self._size

		last_dp = image.shape[0]
		for i in range(self._steps):
			current_dp, lost = self._track(image, current, _size)
			avg = average(current_dp, self._model_weights)
			
			if avg.length < 1 or avg.length > last_dp or avg.length > _size:
				break
			_size = int(_size * self._sizemul)
			res = current_dp - avg
			var = average( [r.sq_length for r in res])
			
			for j, dp in enumerate(res):
				if j in lost or dp.sq_length > max(var * self._r_sigma, 1):
					current_dp[j] = avg
			current += current_dp
			last_dp = avg.length

		delta_pos = current - self._model_coords
		center = image.shape[1]/2, image.shape[0]/2
		c_previous = self._model_coords - center
		c_current = current - center

		dot = np.nansum(np.multiply(c_previous, c_current), axis= 1)
		cross = np.cross(c_previous, c_current)
		delta_angle = np.arctan2(cross,  dot)

		return TrackingSolution.create(delta_pos= delta_pos, 
											delta_angle= delta_angle, 
											image_size= image.shape, 
											lost_indices= lost,
											weights= self._model_weights,
											rejection_sigma= self._r_sigma,
											rejection_iter= self._r_iter)

# todo: move elsewhere
_Method = Literal['hough', 'hough_adaptive', 'hough_threshold']
class GlobalAlignmentTracker(Tracker):
	sigma : int
	iterations : int
	tolerance : float
	
	_detector : StarDetector
	_method : CongruenceMethod

	def __init__(self, detection_method : _Method | StarDetector = 'hough',
							congruence_method: Literal['sss', 'sas', 'aaa'] = 'sss',
							congruence_tolerance : float = 0.05,
							area_weight : bool = True,
							rejection_sigma= 3, rejection_iter= 3,  **detector_args) -> None:
		self.sigma = rejection_sigma
		self.iterations = rejection_iter
		self.tolerance = congruence_tolerance
		
		if congruence_method == 'sas':
			self._method = congruence_sas
		elif congruence_method == 'sss':
			self._method = congruence_sss
		elif congruence_method == 'aaa':
			self._method = congruence_aaa
		else:
			raise ValueError(f'Unsupported congruence method "{self._method}" available options are sss, sas and aaa')
		
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

	def setup_model(self, stars: StarList, **kwargs):
		if len(stars) <= 3:
			raise RuntimeError(f'Model of {type(self).__name__} requires more than 3 stars to set up')
		
		coords = stars.positions
		self._indices = k_neighbors(coords, 2)
		self._model = list[PositionArray]()
		
		for idx in self._indices:
			coord = coords[idx]
			coord.close()
			self._model.append(coord)

		if self._use_w:
			self._areas = np.array([area(trig) for trig in self._model])

	def track(self, image: ImageLike) -> TrackingSolution:
		''' 
			Based on "Efficient k-Nearest Neighbors (k-NN) Solutions with NumPy" by Peng Qian (2023)
			https://www.dataleadsfuture.com/efficient-k-nearest-neighbors-k-nn-solutions-with-numpy/
		'''
		detected_stars = self._detector.detect(image)
		if len(detected_stars) <= 3:
			print('Less than 3 stars were detected for this image')
			return TrackingSolution.identity()
		
		coords = detected_stars.positions
		indices = k_neighbors(coords, 2)
		triangles : List[PositionArray] = [coords[idx] for idx in indices]
		
		# !warning: slow code
		matched = list[Tuple[int, int]]()
		for i, trig1 in enumerate(self._model):
			for j, trig2 in enumerate(triangles):
				if self._method(trig1, trig2, self.tolerance):
					matched.append((i, j))
					break
		if len(matched) == 0:
			print('No triangles were matched for this image')
			return TrackingSolution.identity()
		
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
			weight_array = tuple(np.repeat(_areas, 3).tolist())
		else:
			weight_array = None

		print(f'Matched {len(matched)} of {len(triangles)} triangles')
		return TrackingSolution.create(delta_pos= delta_pos,
											delta_angle= delta_rot,
											image_size= image.shape,
											weights= weight_array,
											rejection_iter= self.iterations,
											rejection_sigma= self.sigma)