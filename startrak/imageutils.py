from typing import Any
import numpy as np

_ImageLike = np.ndarray[Any, np.dtype[np.int_]]	# todo: Unify typing aliases
__all__ = ['sigma_stretch']
def sigma_stretch(image : _ImageLike, sigma=1.0):
	'''
		Sigma clipping stretch algorithm

		Parameters:
		- image (arraylike) : The image to stretch
		- sigma (float, default: 1): Sigma factor to consider black and white values from the median of the input image, described by the formula: clip = median +- sigma * std
	'''
	median = np.median(image)
	std = np.std(image)
	smin = median - sigma * std
	smax = median + sigma * std
	image = np.clip((image - smin) * (255 / (smax - smin)), 0, 255)
	return image.astype(np.uint8)