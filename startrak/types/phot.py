# compiled module

from math import pi
import numpy as np
from startrak.types import PhotometryBase, Star
from startrak.types.alias import ImageLike

def _get_cropped(img : ImageLike, star : Star, padding : int = 0) -> ImageLike:
		rmin, rmax = star.position[1] - star.aperture - padding, star.position[1] + star.aperture + padding
		cmin, cmax = star.position[0] - star.aperture - padding, star.position[0] + star.aperture + padding
		return img[rmin:rmax, cmin:cmax].copy()

class AperturePhot(PhotometryBase):
	''' Aperture photometry with sigma clipping'''
	width : int
	offset : int
	sigma : int

	def __init__(self, width : int, offset : int, sigma : int = 0) :
		self.width = width
		self.offset = offset
		self.sigma = sigma
	
	def evaluate(self, img: ImageLike, star: Star) -> float | int:
		_offset = (self.width + self.offset)
		crop = _get_cropped(img, star, _offset)
		_y, _x = np.ogrid[:crop.shape[0], :crop.shape[1]]
		_sqdst = (_x -  crop.shape[0]/2) **2 + (_y - crop.shape[1]/2) **2
		_sqapert = star.aperture ** 2
		circle_mask = _sqdst < _sqapert
		annulus_mask = (_sqdst >= _sqapert + self.offset) & (_sqdst < _sqapert + _offset)
		
		if self.sigma != 0:
			sigma_mask = np.abs(crop - np.nanmean(crop)) < np.nanstd(crop) * self.sigma
			crop = crop[sigma_mask]
		bg_flux = np.nanmean(crop[annulus_mask])
		flux = np.nanmean(crop[circle_mask])
		return float(flux - bg_flux)


class BackgroundOnlyPhot(PhotometryBase):
	''' Extracts the background used by aperture photometry'''
	width : int
	offset : int
	sigma : int

	def __init__(self, width : int, offset : int, sigma : int = 0) :
		self.width = width
		self.offset = offset
		self.sigma = sigma
	
	def evaluate(self, img: ImageLike, star: Star) -> float | int:
		_offset = (self.width + self.offset)
		crop = _get_cropped(img, star, _offset)
		_y, _x = np.ogrid[:crop.shape[0], :crop.shape[1]]
		_sqdst = (_x -  crop.shape[0]/2) **2 + (_y - crop.shape[1]/2) **2
		_sqapert = star.aperture ** 2

		annulus_mask = (_sqdst >= _sqapert + self.offset) & (_sqdst < _sqapert + _offset)
		if self.sigma != 0:
			sigma_mask = np.abs(crop - np.nanmean(crop)) < np.nanstd(crop) * self.sigma
			crop = crop[sigma_mask]
		bg_flux = np.nanmean(crop[annulus_mask])
		return float(bg_flux)
	
class SimplePhot(PhotometryBase):
	''' Uncalibrated photomery, returns the integrated flux of the star without background removal or sigma clipping'''
	padding : int

	def __init__(self, padding : int = 0) -> None:
		self.padding = 0
	
	def evaluate(self, img: ImageLike, star: Star) -> float | int:
		crop = _get_cropped(img, star, self.padding)
		_y, _x = np.ogrid[:crop.shape[0], :crop.shape[1]]
		_sqdst = (_x -  crop.shape[0]/2) **2 + (_y - crop.shape[1]/2) **2
		_sqapert = star.aperture ** 2
		circle_mask = _sqdst < _sqapert
		flux = np.nanmean(crop[circle_mask])
		return float(flux)