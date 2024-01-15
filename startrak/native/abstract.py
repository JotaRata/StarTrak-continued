# compiled module
from __future__ import annotations
from typing import List, Optional, Self, Sequence, Tuple, final
from abc import ABC, ABCMeta, abstractmethod

from startrak.native.alias import ImageLike
from startrak.native.classes import FileInfo, Header, HeaderArchetype, PhotometryResult, Star, TrackingSolution
from startrak.native.collections.position import Position, PositionArray, PositionLike
from startrak.native.collections.starlist import StarList
from startrak.native.collections.filelist import FileList
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
	included_files : FileList
	included_stars : StarList
	
	def __init__(self, name : str):
		if type(self) is Session:
			raise NotImplementedError('Cannot create object of abtsract type "Session"')
		self.name = name
		self.archetype : HeaderArchetype = None
		self.included_files = FileList()
		self.included_stars = StarList()


	def add_file(self, *items : FileInfo): 
		if len(items) == 0:
				print('No files were added')
				return
		
		_added = [item for item in items if type(item) is FileInfo]
		if len(self.included_files) == 0:
			first = _added[0]
			self.set_archetype(first.header)
		
		self.included_files.extend(_added)
		self.__item_added__(_added)

	def remove_file(self, *items : FileInfo): 
		if len(items) == 0:
				print('No files were removed')
				return
		
		_removed = [item for item in items if type(item) is FileInfo]
		self.included_files.remove_many(_removed)
		self.__item_removed__(_removed)

	def add_star(self, *stars : Star):
		if len(stars) == 0:
			print('No stars were added')
			return
		self.included_stars.extend(stars)

	def remove_star(self, *stars : Star):
		self.included_stars.remove_many(stars)
	
	def set_archetype(self, header : Optional[Header]):
		if header is None: 
			self.archetype = None
			return
		self.archetype = HeaderArchetype(header)

	@abstractmethod
	def __item_added__(self, added : Sequence[FileInfo]): 
		raise NotImplementedError()
	@abstractmethod
	def __item_removed__(self, removed : Sequence[FileInfo]): 
		raise NotImplementedError()
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		obj = cls(attributes['name'])
		for attr, value in attributes.items():
			setattr(obj, attr, value)
		return obj
	
	def __export__(self) -> AttrDict:
		return {'archetype' : self.archetype,'included_files': self.included_files, 'included_stars': self.included_stars}
	
	def __pprint__(self, indent: int, expand_tree : int) -> str:
		return super().__pprint__(indent, expand_tree)

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
	