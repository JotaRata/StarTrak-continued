
from math import pi
import numpy as np
from startrak.native import PhotometryBase, PhotometryResult, Star
from startrak.native.alias import ImageLike
from startrak.native.collections import Position, PositionLike

def _get_cropped(img : ImageLike, position : Position | PositionLike, aperture: float, padding : int = 0, fillnan= True) -> ImageLike:
		rmin, rmax = position[1] - aperture - padding, position[1] + aperture + padding
		cmin, cmax = position[0] - aperture - padding, position[0] + aperture + padding
		
		rmin, rmax = int(rmin), int(rmax)
		cmin, cmax = int(cmin), int(cmax)
		if ((rmin < 0 or rmax > img.shape[0]) or (cmin < 0 or cmax > img.shape[1])) and fillnan:
			padr = max(-rmin + 1, 0), max(rmax - img.shape[0], 0)
			padc = max(-cmin + 1, 0), max(cmax - img.shape[1], 0)
			
			padded_img = np.pad(img.astype(float), [padr, padc], mode= 'constant', constant_values= np.nan)
			return padded_img[rmin + padr[0] :rmax + padr[1] + padr[0], cmin + padc[0]: cmax + padc[1] + padc[0]]
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
	
	def evaluate(self, img: ImageLike, position : Position | PositionLike, aperture: int) -> PhotometryResult:
		_offset = (self.width + self.offset)
		crop = _get_cropped(img, position, aperture, _offset)
		_y, _x = np.ogrid[:crop.shape[0], :crop.shape[1]]
		_sqdst = (_x -  crop.shape[0]/2) **2 + (_y - crop.shape[1]/2) **2
		_sqapert = aperture ** 2
		circle_mask = _sqdst < _sqapert
		annulus_mask = (_sqdst >= _sqapert + self.offset) & (_sqdst < _sqapert + _offset)
		
		flux_raw = crop[circle_mask]
		bg_flux = crop[annulus_mask]
		if self.sigma != 0:
			sigma_mask = np.abs(bg_flux - np.nanmean(bg_flux)) < np.nanstd(bg_flux) * self.sigma
			bg_flux = bg_flux[sigma_mask]
		return PhotometryResult(flux= float(np.nanmean(flux_raw) - np.nanmean(bg_flux)),
										flux_raw= float(np.nanmean(flux_raw)),
										flux_range= float(np.nanpercentile(flux_raw, 75) - np.nanpercentile(flux_raw, 25)),
										background= float(np.nanmean(bg_flux)),
										background_sigma= float(np.nanstd(bg_flux))
										)
