from typing import Any, Callable, List, Literal, Tuple
from numpy.typing import NDArray
from startrak.types import Star
from startrak.imageutils import sigma_stretch
import numpy as np
import cv2

from startrak.types.alias import ImageLike, Decorator

__all__ = ['detect_stars', 'get_methods', 'detection_method']
__methods__ = dict[str, Callable[..., List[Star]]]() # type: ignore
_DetectionMethod = Callable[..., List[Star]]

def detect_stars(image : ImageLike, method : Literal['adaptive', 'threshold'] = 'adaptive', *args, **kwargs) -> List[Star]:
	'''
		## Automatic star detection.
		Avaiable methods are 'adaptive' and 'threshold' that corresponds to 'Adaptive HoughCircles' and 'Simple HoughCircles' respectively.

		Returns: A list containing the detected stars

		---
		### Adaptive Threshold + Hough Circles method
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
			
		### Simple Threshold + Hough Circles method
		This method uses OpenCV threshold function on a blurred and stretched version of the image using a gaussian kernel, then it uses the HughCircles algorithm to detect features in the image.

		This method is suitable for processed images that have no noticeable background gradient.

		Parameters:
		- image (arrayLike): The input image to detect features from
		- threshold (float[0..1]): The brightness percentage that determines which stars are bright enough to be included
		- sigma (float, default: 1): Sigma value for the contrast stretch algorithm, smaller values will make the stars more prominent but it will also increase the noise.
		- min/max_size (int, default: 5 and 15): Minimum and maximum sizes respectively for the Hugh Circles algorithm to detect stars (scales with downsampling).
		- downs (int, default: 512): Downsampling resolution, set it to None will use the original image size (slower)
		- ksize (int/odd number, default: 15): The size of the gaussian kernel used to blur the image (scales with downsampling).
		- min_dst (int, default: 16): The minimum distance in pixels detected stars should be, stars closer than this value will be ignored (scales with downsampling).
	'''
	return __methods__[method](image, *args, **kwargs) # type: ignore

def get_methods() -> Tuple[_DetectionMethod, ...]:
	'''
		Get a list of registered detection methods
		see: @detect_stars
	'''
	return tuple(__methods__.values())

# decorator method
def detection_method(id : str, name : str) -> Decorator[List[Star]]:
	def decorator(func : Callable[..., List[Star]]) -> _DetectionMethod:
		def wrapper(*args : Any, **kwargs : Any):
			return func(*args, **kwargs)
		wrapper.name = name  # type: ignore
		__methods__[id] = wrapper
		return wrapper
	return decorator

# ------------------------- Methods ---------------------
@detection_method('adaptive', 'Adaptive HoughCircles')
def adaptive_hough_circles( image : ImageLike, sigma : float = 3.0,
						min_size : int = 5, max_size : int = 15,
						downs : int = 512, ksize : int = 15, min_dst : int = 16,
						threshold : int = 2, blockSize : int = 11) -> list[Star]:
	if downs is not None and downs != 0:
		_f = downs / np.min(image.shape) 
		image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	else: _f = 1
	image = sigma_stretch(image, sigma=sigma)

	image = cv2.GaussianBlur(image, (ksize, ksize), 0)
	image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=blockSize, C=threshold)
	
	circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, min_dst, param1=100, param2=min_size * 2, minRadius=min_size, maxRadius=max_size)
	
	if circles is not None:
		_c = circles[0, :].copy()
		return [Star(str(i), (int(c[0] / _f), int(c[1] / _f)), int(c[2] / _f)) for i, c in enumerate(_c)]
	print('No stars were detected, try changing min/max sizes or decreasing the sigma value')
	return list[Star]()
	
@detection_method('threshold', 'Simple HoughCircles')
def simple_hough_circles( image : ImageLike, threshold : float,
							sigma : int = 1, min_size : int = 5, max_size : int = 15,
							downs : int = 512, ksize : int = 15, min_dst : int = 16) -> list[Star]:
	if downs is not None and downs != 0:
		_f = downs / np.min(image.shape) 
		image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	else: _f = 1
	image = sigma_stretch(image, sigma)
	image = cv2.GaussianBlur(image, (ksize, ksize), 0)
	_, image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

	circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, min_dst, param1=100, param2=min_size * 2, minRadius=min_size, maxRadius=max_size)
	
	if circles is not None:
		_c : NDArray = circles[0, :].copy()
		return [Star(str(i), (int(c[0] / _f), int(c[1] / _f)), int(c[2] / _f)) for i, c in enumerate(_c)]
	print('No stars were detected, try changing min/max sizes or decreasing the sigma value')
	return list[Star]()

def visualize_stars(image : ImageLike, stars : List[Star],
					vsize : int= 720, sigma : int = 4):
	if vsize is not None and vsize != 0:
		_f = vsize / np.min(image.shape) 
		image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	else: _f = 1
	image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
	image = sigma_stretch(image, sigma=sigma)
	for star in stars:
		pos = int(star.position[0] * _f), int(star.position[1] * _f)
		rad = int(star.aperture * _f)
		image = cv2.putText(image, star.name, (pos[0], pos[1] - rad-4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 0), 1)
		image = cv2.circle(image, pos, rad, (200, 0, 0), 2)
	cv2.imshow('Visualize stars', image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()