# compiled module
from __future__ import annotations
from typing import Callable, List, Optional, Self, Sequence, Tuple, final
from abc import ABC, ABCMeta, abstractmethod

from startrak.native.alias import ImageLike, ValueType
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
	working_dir : str
	use_relative : bool
	archetype : Optional[HeaderArchetype]
	included_files : FileList
	included_stars : StarList
	force_validation : bool
	on_validationFailed : Callable[[str, ValueType, ValueType], None] | None
	
	def __init__(self, name : str, working_dir : str, force_validation : bool = False, use_relativePaths : bool = False):
		if type(self) is Session:
			raise NotImplementedError('Cannot create object of abtsract type "Session"')
		self.name = name
		self.working_dir = working_dir
		self.archetype : HeaderArchetype = None
		self.force_validation = force_validation
		self.use_relative = use_relativePaths
		self.on_validationFailed = None
		self.included_files = FileList()
		self.included_stars = StarList()

	def add_file(self, *items : FileInfo): 
		if len(items) == 0:
				print('No files were added')
				return
		
		added = list[FileInfo]()
		for item in items:
			if not self._validate_file(item):
				continue
			if len(added) == 0 and len(self.included_files) == 0:
				self.set_archetype(item.header)
			added.append(item)
		self.included_files.extend(added)
		self.__item_added__(added)

	def remove_file(self, *items : FileInfo): 
		if len(items) == 0:
				print('No files were removed')
				return
		
		_removed = [item for item in items if isinstance(item, FileInfo)]
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
	
	def _validate_file(self, file : FileInfo) -> bool:
		if not isinstance(file, FileInfo):
			return False
		if self.force_validation and self.archetype:
			return self.archetype.validate(file.header, self.on_validationFailed)
		return True

	@abstractmethod
	def __on_saved__(self, output_path : str): 
		raise NotImplementedError()
	@abstractmethod
	def __item_added__(self, added : Sequence[FileInfo]): 
		raise NotImplementedError()
	@abstractmethod
	def __item_removed__(self, removed : Sequence[FileInfo]): 
		raise NotImplementedError()
	
	@classmethod
	def __import__(cls, attributes: AttrDict, **cls_kw) -> Self:
		session= cls(attributes['name'], attributes['working_dir'], force_validation= attributes['force_validation'], 
					use_relativePaths= attributes['use_relativePaths'], **cls_kw)
		session.archetype = attributes['archetype']
		session.included_files = attributes['included_files']
		session.included_stars = attributes['included_stars']
		return session
	
	def __export__(self) -> AttrDict:
		return {
			'name': self.name, 
			'archetype' : self.archetype,
			'included_files': self.included_files, 
			'included_stars': self.included_stars, 
			'working_dir' : self.working_dir,
			'force_validation' : self.force_validation,
			'use_relativePaths' : self.use_relative}
	
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
	