from typing import Any, Callable, List
from numpy.typing import NDArray
import numpy as np
from numpy.typing import NDArray
import cv2
from startrak.types import Star

__methods = dict[str, tuple]()
def detection_method(id : str, name : str):
	def decorator(func : Callable[..., Any]):
		__methods[id] = name, func
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		return wrapper
	return decorator
def contrast_stretch(image : NDArray[np.int_], sigma=1.0):
	median = np.median(image)
	std = np.std(image)
	smin = median - sigma * std
	smax = median + sigma * std
	image = np.clip((image - smin) * (255 / (smax - smin)), 0, 255)
	return image.astype(np.uint8)

@detection_method('adaptive', 'Adaptive HoughCircles')
def adaptive_hough_circles( image : NDArray[np.int_], sigma : float = 3.0,
						min_size : int = 5, max_size : int = 15,
						downs : int = 512, ksize : int = 15, min_dst : int = 16,
						threshold : int = 2, blockSize : int = 11):
	'''
		## Adaptive Threshold + Hough Circles method
		This method uses OpenCV adaptive threshold on a blurred and stretched version of the image using a gaussian kernel, then it uses the HughCircles algorithm to detect features in the image.

		This method is suitable for images with a promitent gradient background or images that haven't been processed with a FLAT field image yet.

		Parameters:
		- image (arrayLike): The input image to detect features from
		- sigma (float, default: 3): Sigma value for the contrast stretch algorithm, smaller values will make the stars more prominent but it will also increase the noise.
		- min/max_size (int, default: 5 and 15): Minimum and maximum sizes respectively for the Hugh Circles algorithm to detect stars (scales with downsampling).
		- downs (int, default: 512): Downsampling resolution, set it to None will use the original image size (slower)
		- ksize (int/odd number, default: 15): The size of the gaussian kernel used to blur the image (scales with downsampling).
		- min_dst (int, default: 16): The minimum distance in pixels detected stars should be, stars closer than this value will be ignored (scales with downsampling).
		- threshold (int, default: 2): Threshold value passed to the cv2.adaptiveThreshold funtion.
		- blockSize (int/odd number, default: 11): blockSize parameter of the cv2.adaptiveThreshold funtion.
		
		Returns: A list containing the detected stars
	'''
	
	if downs is not None and downs != 0:
		_f = downs / np.min(image.shape) 
		image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	else: _f = 1
	image = contrast_stretch(image, sigma=sigma)

	image = cv2.GaussianBlur(image, (ksize, ksize), 0)
	image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=blockSize, C=threshold)
	
	circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, min_dst, param1=100, param2=min_size * 2, minRadius=min_size, maxRadius=max_size)
	
	if circles is not None:
		_c : NDArray = circles[0, :].copy()
		return [Star(str(i), (int(c[0] / _f), int(c[1] / _f)), int(c[2] / _f)) for i, c in enumerate(_c)]
	print('No stars were detected, try changing min/max sizes or decreasing the sigma value')
	return List[Star]()
	
def visualize(image : NDArray[np.int_], stars : List[Star],
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