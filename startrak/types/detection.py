
from typing import List, Tuple

import cv2
from startrak.imageutils import sigma_stretch
from startrak.native import StarDetector
from startrak.native.alias import ImageLike
from startrak.native import PositionArray


class HoughCircles(StarDetector):
	_sigma : float
	_ksize : Tuple[int, int] | None
	_min_dst : float
	_min_size : int
	_max_size : int
	_dp : int
	_p1 : float
	_p2 : float
	
	def __init__(self, *, sigma= 4, kernel= 15, dp= 1, min_dst= 16, min_radius= 4, max_radius= 16, 
					param1= 100, param2= 10) -> None:
		assert sigma > 0, "sigma must be greater than zero"
		self._sigma = sigma
		assert min_dst > 0, "min_dst must be greater than zero"
		self._min_dst = min_dst
		assert min_radius > 0, "min_radius must be greater than zero"
		assert max_radius > min_radius, "max_radius must be greater than min_dst"
		self._min_size = min_radius
		self._max_size = max_radius
		assert kernel % 2 != 0, "kernel must be an odd number"
		self._ksize = kernel, kernel
		if kernel == 0:
			self._ksize = None

		self._p1 = param1
		self._p2 = param2
		self._dp = dp
	
	def _detect(self, image : ImageLike) -> Tuple[PositionArray, List[float]]:
		img = sigma_stretch(image, sigma= self._sigma)
		if self._ksize is not None:
			img = cv2.GaussianBlur(img, self._ksize, 0)

		circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1,
										minDist= self._min_dst, param1= self._p1, param2= self._p2, minRadius= self._min_size, maxRadius= self._max_size)
		return PositionArray(*circles[0][:, :2]), circles[0][:, 2].tolist()
	
class AdaptiveHoughCircles(HoughCircles):
	_block_size : int
	_threshold : int

	def __init__(self, *, block_size= 13, threshold= 2, **kwargs) -> None:
		assert block_size % 2 != 0, "block_size must be an odd number"
		self._block_size = block_size
		assert threshold > 0, "threshold must be greater than zero"
		self._threshold = threshold
		super().__init__(**kwargs)

	def _detect(self, image : ImageLike) -> Tuple[PositionArray, List[float]]:
		img = sigma_stretch(image, sigma= self._sigma)
		if self._ksize is not None:
			img = cv2.GaussianBlur(img, self._ksize, 0)
		img = cv2.adaptiveThreshold(img, 
											255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize= self._block_size, C= self._threshold)
		circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1,
										minDist= self._min_dst, param1= self._p1, param2= self._p2, minRadius= self._min_size, maxRadius= self._max_size)
		return PositionArray(*circles[0][:, :2]), circles[0][:, 2].tolist()

class ThresholdHoughCircles(HoughCircles):
	_threshold : int

	def __init__(self, *,  threshold= 2, **kwargs) -> None:
		assert threshold > 0, "threshold must be greater than zero"
		self._threshold = threshold
		super().__init__(**kwargs)

	def _detect(self, image : ImageLike) -> Tuple[PositionArray, List[float]]:
		img = sigma_stretch(image, sigma= self._sigma)
		if self._ksize is not None:
			img = cv2.GaussianBlur(img, self._ksize, 0)
		_, img = cv2.threshold(img, self._threshold, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1,
										minDist= self._min_dst, param1= self._p1, param2= self._p2, minRadius= self._min_size, maxRadius= self._max_size)
		return PositionArray(*circles[0][:, :2]), circles[0][:, 2].tolist()
	
