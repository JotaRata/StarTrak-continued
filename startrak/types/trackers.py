from typing import Any, List, Optional, Tuple
from startrak.types import Star, TrackingMethod, TrackingModel
from startrak.types.alias import Position

class SimpleTracker(TrackingMethod):
	track_size : int
	var_thresold : float
	_model : TrackingModel
	_star_values : List[float]

	def __init__(self, tracking_size : int, variation : float) -> None:
		self.track_size = tracking_size
		self.var_thresold = variation
		self._model = TrackingModel()
		self._star_values = list[float]()
	
	def setup_model(self, stars: List[Star], *args: Tuple):
		assert len(stars) >= 3, 'There should be at least three trackable stars'
		self._model.vertices = [star.position for star in stars]
		# todo: setup star brighness values
		
