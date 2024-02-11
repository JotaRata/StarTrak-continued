
import numpy as np
from startrak.native import PhotometryBase, PhotometryResult
from startrak.native.alias import ImageLike
from startrak.native import Position, PositionLike

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
		
		flux_array = crop[circle_mask]
		bkg_array = crop[annulus_mask]
		if self.sigma != 0:
			sigma_mask = np.abs(bkg_array - np.nanmean(bkg_array)) < np.nanstd(bkg_array) * self.sigma
			bkg_array = bkg_array[sigma_mask]
		
		# NaN functions used
		flux_mean = float(np.nanmean(flux_array))
		flux_sigma= float(np.nanstd(flux_array))
		flux_max= float(np.nanmax(flux_array))

		bkg_mean = float(np.nanmean(bkg_array))
		bkg_sigma = float(np.nanstd(bkg_array))
		bkg_max = float(np.nanmax(bkg_array))

		return PhotometryResult.new(flux= 				flux_mean - bkg_mean,
											flux_sigma= 		flux_sigma,
											flux_raw= 			flux_mean,
											flux_max= 			flux_max,
											background= 		bkg_mean,
											background_sigma= bkg_sigma,
											background_max= 	bkg_max,
											method= 'aperture',
											aperture_radius= aperture,
											annulus_width= self.width,
											annulus_offset= self.offset
											)
