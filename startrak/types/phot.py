# compiled module

from math import pi
import numpy as np
from startrak.types import PhotMethod, Star
from startrak.types.alias import ImageLike


class SimplePhot(PhotMethod):
	width : int
	offset : int

	def __init__(self, width : int, offset : int) -> None:
		self.width = width
		self.offset = offset
	
	def evaluate(self, img: ImageLike, star: Star):
		_offset = (self.width + self.offset)
		rmin, rmax = star.position[1] - star.aperture - _offset, star.position[1] + star.aperture + _offset
		cmin, cmax = star.position[0] - star.aperture - _offset, star.position[0] + star.aperture + _offset
		crop = img[rmin:rmax, cmin:cmax].copy()
		
		_y, _x = np.ogrid[:crop.shape[0], :crop.shape[1]]
		radial_dst = np.sqrt((_x -  crop.shape[0]/2) **2 + (_y - crop.shape[1]/2) **2)
		circle_mask = radial_dst < star.aperture
		annulus_mask = (radial_dst >= star.aperture + self.offset) & (radial_dst < star.aperture + _offset)
		# crop[~(annulus_mask | circle_mask)] = 0
		
		bg_flux = np.nanmean(crop[annulus_mask])
		flux = np.nanmean(crop[circle_mask])

		return float(flux - bg_flux)

