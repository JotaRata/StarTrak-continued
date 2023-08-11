from typing import List
from numpy.typing import NDArray
import numpy as np
from numpy.typing import NDArray
import cv2
from startrak.types import Star

def contrast_stretch(image : NDArray, sigma=1.0):
	median = np.median(image)
	std = np.std(image)
	smin = median - sigma * std
	smax = median + sigma * std
	image = np.clip((image - smin) * (255 / (smax - smin)), 0, 255)
	return image.astype(np.uint8)

def detect_stars( image : NDArray[np.int_], sigma : float = 3.0,
						min_size : int = 5, max_size : int = 15,
						downs : int = 512, ksize : int = 15, min_dst : int = 16,
						threshold : int = 2, blockSize : int = 11):
	_f = downs / np.min(image.shape) 
	image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	image = contrast_stretch(image, sigma=sigma)

	image = cv2.GaussianBlur(image, (ksize, ksize), 0)
	image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=blockSize, C=threshold)
	
	circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, min_dst, param1=100, param2=min_size * 2, minRadius=min_size, maxRadius=max_size)
	
	if circles is not None:
		_c : NDArray = circles[0, :].copy()
		return [Star(str(i), (int(c[0] / _f), int(c[1] / _f)), int(c[2] / _f)) for i, c in enumerate(_c)]
	print('No stars were detected, try decreasing the sigma value')
	return List[Star]()
	
def visualize(image : NDArray[np.uint8], stars : List[Star],
					vsize : int= 720):
	if vsize is not None and vsize != 0:
		_f = vsize / np.min(image.shape) 
		image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	else: _f = 1
	image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
	image = contrast_stretch(image, sigma=4)
	for star in stars:
		pos = int(star.position[0] * _f), int(star.position[1] * _f)
		rad = int(star.aperture * _f)
		image = cv2.circle(image, pos, rad, (200, 0, 0), 2)
	cv2.imshow('Visualize stars', image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()