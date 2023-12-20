from typing import List, Literal, Tuple
from startrak.native import PhotometryBase, Star, StarDetector, StarList
from startrak.imageutils import sigma_stretch
from startrak.types import detection
from startrak.types import phot
import numpy as np
import cv2

from startrak.native.alias import ImageLike

__all__ = ['detect_stars', ]
_Method = Literal['hough', 'hough_adaptive', 'hough_threshold']

def detect_stars(image : ImageLike, 
					  method : _Method | StarDetector = 'hough', photometry : Literal['aperture']|PhotometryBase|None = 'aperture', **detector_args) -> StarList:
	_detector : StarDetector
	# todo: replace with dict based mapping
	if method == 'hough':
		_detector = detection.HoughCircles(**detector_args)
	elif method == 'hough_adaptive':
		_detector = detection.AdaptiveHoughCircles(**detector_args)
	elif method == 'hough_threshold':
		_detector = detection.ThresholdHoughCircles(**detector_args)
	elif isinstance(method, StarDetector):
		_detector = method
	else:
		raise ValueError(method)
	
	stars = _detector.detect(image)
	if photometry:
		phot_method : PhotometryBase
		if photometry == 'aperture':
			phot_method = phot.AperturePhot(4, 1, 0)
		else:
			phot_method = photometry
		for star in stars:
			star.photometry = phot_method.evaluate_star(image, star)
	return stars

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