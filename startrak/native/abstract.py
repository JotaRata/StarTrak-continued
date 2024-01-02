# compiled module
from typing import IO, List, Optional, Self, Set, Tuple, final
from abc import ABC, ABCMeta, abstractmethod

from startrak.native.alias import ImageLike
from startrak.native.classes import FileInfo, Header, HeaderArchetype, PhotometryResult, Star, TrackingSolution
from startrak.native.collections.position import Position, PositionArray, PositionLike
from startrak.native.collections.starlist import StarList
from startrak.native.ext import AttrDict, STObject

from mypy_extensions import mypyc_attr


@mypyc_attr(allow_interpreted_subclasses=True)
class PhotometryBase(ABC):
	@abstractmethod
	def evaluate(self, img : ImageLike, position : Position | PositionLike, aperture: int) -> PhotometryResult:
		pass

	def evaluate_star(self, img : ImageLike, star : Star) -> PhotometryResult:
		return self.evaluate(img, star.position, star.aperture)
	
@mypyc_attr(allow_interpreted_subclasses=True)
class Tracker(ABC):
	@abstractmethod
	def setup_model(self, stars : StarList, **kwargs):
		pass
	@abstractmethod
	def track(self, image : ImageLike) -> TrackingSolution:
		pass

@mypyc_attr(allow_interpreted_subclasses=True)
class StarDetector(ABC):
	star_name : str = 'star_'
	@abstractmethod
	def _detect(self, image : ImageLike) -> Tuple[PositionArray, List[float]]:
		raise NotImplementedError()

	@final
	def detect(self, image : ImageLike) -> StarList:
		positions, apertures = self._detect(image)
		if len(positions) == 0:
			print('No stars were detected, try adjusting the parameters')
			return StarList()
		return StarList( *[Star(self.star_name + str(i), positions[i], int(apertures[i])) 
					for i in range(len(positions))])


#region Sessions
@mypyc_attr(allow_interpreted_subclasses=True)
class Session(STObject, metaclass= ABCMeta):
	archetype : Optional[HeaderArchetype]
	included_items : Set[FileInfo]
	
	def __init__(self, name : str):
		if type(self):
			raise NotImplementedError('Cannot create object of abtsract type "Session"')
		self.name = name
		self.archetype : HeaderArchetype = None
		self.included_items : set[FileInfo] = set()

	def add_item(self, item : FileInfo | List[FileInfo]): 
		if type(item) is list:
			_items = item
		elif type(item) is FileInfo:
			_items = [item]
		else: raise TypeError()
		_added = {_item for _item in _items if type(_item) is FileInfo}
		if len(self.included_items) == 0:
			first = next(iter(_added))
			assert isinstance(first, FileInfo)
			self.set_archetype(first.header)
		
		self.included_items |= _added
		self.__item_added__(_added)
		# todo: raise warning if no items were added

	def remove_item(self, item : FileInfo | List[FileInfo]): 
		if type(item) is list:
			_items = item
		elif type(item) is FileInfo:
			_items = [item]
		else: raise TypeError()
		_removed = {_item for _item in _items if type(_item) is FileInfo}
		self.included_items -= _removed
		self.__item_removed__(_removed)
	
	def set_archetype(self, header : Optional[Header]):
		if header is None: 
			self.archetype = None
			return
		self.archetype = HeaderArchetype(header)

	@abstractmethod
	def __item_added__(self, added : Set[FileInfo]): 
		raise NotImplementedError()
	@abstractmethod
	def __item_removed__(self, removed : Set[FileInfo]): 
		raise NotImplementedError()
	@abstractmethod
	def save(self, out : str): 
		raise NotImplementedError()
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		obj = cls(attributes['name'])
		for attr, value in attributes.items():
			setattr(obj, attr, value)
		return obj

#endregion

@mypyc_attr(allow_interpreted_subclasses=True)
class STExporter(ABC):
	@abstractmethod
	def __enter__(self) -> Self:
		raise NotImplementedError()
	
	@abstractmethod
	def __exit__(self, *args) -> None:
		raise NotImplementedError()
	
	@abstractmethod
	def write(self, obj : STObject):
		raise NotImplementedError()
	
@mypyc_attr(allow_interpreted_subclasses=True)
class STImporter(ABC):
	@abstractmethod
	def __enter__(self) -> Self:
		raise NotImplementedError()
	
	@abstractmethod
	def __exit__(self, *args) -> None:
		raise NotImplementedError()
	
	@abstractmethod
	def read(self) -> STObject:
		raise NotImplementedError()
	