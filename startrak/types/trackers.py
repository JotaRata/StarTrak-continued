from random import randint, uniform
from typing import Any, List, Literal, Sequence, Tuple
import numpy as np
from startrak.native.classes import TrackingSolution
from startrak.native.numeric import average

from startrak.native.utils.geomutils import *
from startrak.native import PhotometryResult, StarDetector, StarList, Tracker, TrackingSolution
from startrak.native.alias import ImageLike
from startrak.native import PositionArray
from startrak.types.phot import _get_cropped
from startrak.types import detection

class PhotometryTracker(Tracker):
	def __init__(self, tracking_size : int, tracking_steps : int = 1, size_mul : float | Literal['auto', 'random'] = 0.5, verbose : bool = False,
							stochasticity : float | None = None, rejection_sigma= 3, rejection_iter= 3) -> None:
		assert tracking_size > 0 and type(tracking_size) is int, 'Tracking size must be a positive integer'
		assert tracking_steps >= 1, 'Tracking steps must be greater or equal than one'
		assert isinstance(size_mul, (float, int)) or (type(size_mul) is str and (size_mul == 'auto' or size_mul=='random')),\
				'Size multiplier must be a real number or literal "auto" | "random"'
		assert stochasticity is None or stochasticity > 0, 'Stochasticity must be a positive number or None'
		assert rejection_iter >= 1, 'Rejection iterations must be greater or equal than one'
		assert rejection_sigma > 0, 'Rejection sigms value must be a positive number'

		self.crop_size = tracking_size
		self.tracking_steps = tracking_steps
		self.rej_sigma = rejection_sigma
		self.rej_iter = rejection_iter
		self.size_mult = size_mul
		self.random_size = stochasticity if stochasticity else 0
		self.verbose = verbose

	# todo: Weights should be inside the Star object, not the tracker
	# todo: Trackers models should contain references to stars
	def setup_model(self, stars: StarList, weights : Sequence[float] | None= None, **kwargs : Any):
		if weights:
			if len(weights) != len(stars):
				raise ValueError('Weights size must be equal to star list size')
			self._model_weights = weights
		else:
			self._model_weights = [1., ] * len(stars)
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

	def track(self, image: ImageLike) -> TrackingSolution:
		start_coords = self._model_coords.copy()
		last_dp = image.shape[0]
		crop_size = self.crop_size

		def track_single():
			current = PositionArray()
			lost = list[int]()
			for i in range(self._model_count): 
				rand_size = int(crop_size * self.random_size)
				rand_offset = randint(-rand_size, rand_size), randint(-rand_size, rand_size)

				crop = _get_cropped(image, start_coords[i] + rand_offset, 0, padding= int(crop_size))
				phot = self._model_phot[i]
				bkg = np.nanmean((np.nanmean(crop[-4:, :]), np.nanmean(crop[:, -4:]), np.nanmean(crop[:4, :]), np.nanmean(crop[:, :4])))
				try:	
					mask = (crop - bkg) > phot.background.sigma * (1 + phot.snr * 2)
					mask &= (crop - bkg) > phot.flux.sigma * (1 + phot.snr) / 2
					mask &= ((crop - bkg) - phot.flux.max) <  phot.flux.sigma
					mask &= ~np.isnan(crop)

					indices = np.transpose(np.nonzero(mask))
					if len(indices) < 16: raise IndexError()
					_w = np.clip(crop[indices[:, 0], indices[:, 1]] - bkg, 0, phot.flux.max) / phot.flux
					_w[np.isnan(_w)] = 0
					avg = np.average(indices, weights= _w ** 2, axis= 0)[::-1]
				except:	#raises ZeroDivisionError and IndexError
					lost.append(i)
					current.append(start_coords[i])
					continue
				current.append(avg - (crop_size,) * 2 + start_coords[i])
			return current - start_coords, lost
		
		def change_size(previous_size : float, lost_indices):
			if isinstance(self.size_mult, (float, int)):
				return previous_size * self.size_mult
			elif self.size_mult == 'auto':
				if previous_size > image.shape[0] / 2:
					return previous_size
				multiplier = 1.5 if len(lost_indices) >= self._model_count // 2 else 0.5
				return previous_size * multiplier
			else:
				return uniform(self.crop_size * 0.5, self.crop_size * 1.5)

		lost_indices = list[int]()
		for i in range(self.tracking_steps):
			current_dp, lost = track_single()
			avg = average(current_dp, [w if n not in lost else 0 for n, w in enumerate(self._model_weights)])
			if self.verbose:
				print(f'iter: {i}, size mode= {self.size_mult} crop size= {crop_size}, lost= {len(lost)}, displacement= {avg.length:.2f}')
			
			if avg.length < 2: # px
				if len(lost) < self._model_count // 2:
					break
			crop_size = change_size(crop_size, lost)
			res = current_dp - avg
			var = average( [r.sq_length for r in res])
			
			for j, dp in enumerate(res):
				if j in lost or dp.sq_length > max(var * self.rej_sigma, 1):
					current_dp[j] = avg
			start_coords += current_dp

		lost_indices = lost #type:ignore
		return TrackingSolution.compute(	start_pos= self._model_coords,
													new_pos = start_coords,
													weights= tuple(self._model_weights),
													lost_indices= lost_indices)

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
		
		coords = PositionArray(* sorted(stars.positions, key= lambda p: p.y))
		self._indices = k_neighbors(coords, 2)
		self._model = list[PositionArray]()
		
		for idx in self._indices:
			coord = coords[idx]
			coord.close()
			self._model.append(coord)

		if self._use_w:
			self._areas = np.array([area(trig) for trig in self._model])

	def track(self, image: ImageLike) -> TrackingSolution:
		detected_stars = self._detector.detect(image)
		if len(detected_stars) <= 3:
			print('Less than 3 stars were detected for this image')
			return TrackingSolution.identity()
		
		coords = PositionArray( *sorted(detected_stars.positions, key= lambda p: p.y))
		indices = k_neighbors(coords, 2)
		triangles : List[PositionArray] = [coords[idx] for idx in indices]
		
		# !warning: slow code
		matched = list[Tuple[int, int]]()
		for i, trig1 in enumerate(self._model):
			for j, trig2 in enumerate(triangles):
				if self._method(trig1, trig2, self.tolerance):
					if 0.99 < area(trig1) / area(trig2) < 1.01:
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

		if self._use_w:
			weight_array = tuple(np.repeat(_areas, 3).tolist())
		else:
			weight_array = None

		print(f'Matched {len(matched)} of {len(triangles)} triangles')
		return TrackingSolution.compute(	start_pos= reference,
													new_pos = current,
													weights= weight_array,
													rejection_iter= self.iterations,
													rejection_sigma= self.sigma)