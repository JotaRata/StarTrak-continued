from startrak.types.alias import *
import numpy as np

__all__ = ['sigma_stretch']

def sigma_stretch(image : ImageLike, sigma=1.0) -> NDArray[np.uint8]:
	'''
		Sigma clipping linear stretch algorithm

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

def linear_stretch(image : ImageLike, smin : NumberLike, smax: NumberLike) -> NDArray[np.uint8]:
	'''
		Linear clipping stretch algorithm

		Parameters:
		- image (arraylike) : The image to stretch
		- smin/smax (scalar): Minimum and maximum values to stretch the input image into the 0..255 range
	'''
	image = np.clip((image - smin) * (255 / (smax - smin)), 0, 255)
	return image.astype(np.uint8)