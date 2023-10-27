from typing import Any, Callable, List, Literal, Tuple
from numpy.typing import NDArray
from startrak.native import Star
from startrak.imageutils import sigma_stretch
import numpy as np
import cv2

from startrak.native.alias import ImageLike, Decorator

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

def visualize_stars(image : ImageLike, stars : List[Star],
					vsize : int= 720, sigma : int = 4, color : Tuple[int, int, int] = (200, 0, 0)):
	if vsize is not None and vsize != 0:
		_f = vsize / np.min(image.shape) 
		image = cv2.resize(image, None, fx=_f, fy=_f, interpolation=cv2.INTER_CUBIC)
	else: _f = 1
	image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
	image = sigma_stretch(image, sigma=sigma)
	for star in stars:
		pos = int(star.position[0] * _f), int(star.position[1] * _f)
		rad = int(star.aperture * _f)
		image = cv2.putText(image, star.name, (pos[0], pos[1] - rad-4), cv2.FONT_HERSHEY_PLAIN, 0.5, color, 1)
		image = cv2.circle(image, pos, rad, color, 2)
	
	def on_click(event, x, y, *_):
		if event == cv2.EVENT_LBUTTONDOWN:
			print(x, y) 
	cv2.namedWindow("image")
	cv2.setMouseCallback('image', on_click) #type:ignore
	cv2.imshow('image', image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()