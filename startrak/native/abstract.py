# compiled module
from __future__ import annotations
import os
from typing import Callable, List, Optional, Self, Sequence, Tuple, final
from abc import ABC, ABCMeta, abstractmethod

from startrak.native.alias import ImageLike, ValueType
from startrak.native.classes import SessionLocationBlock, FileInfo, Header, HeaderArchetype, PhotometryResult, RelativeContext, Star, TrackingSolution
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
	_session_path : SessionLocationBlock
	archetype : Optional[HeaderArchetype]
	included_files : FileList
	included_stars : StarList
	force_validation : bool
	on_validationFailed : Callable[[str, ValueType, ValueType], None] | None
	
	def __init__(self, name : str, working_dir : str, force_validation : bool = False, use_relativePaths : bool = False):
		if type(self) is Session:
			raise NotImplementedError('Cannot create object of abtsract type "Session"')
		self.name = name
		self.archetype : HeaderArchetype = None
		self.force_validation = force_validation
		self.on_validationFailed = None
		self._session_path = SessionLocationBlock(working_dir.replace('\\', '/'), use_relativePaths)
		self.included_files = FileList()
		self.included_stars = StarList()

	@property
	def working_dir(self) -> str:
		return self._session_path.session_path
	@working_dir.setter
	def working_dir(self, value):
		self._session_path = SessionLocationBlock(value, self._session_path.uses_relative)
	@property
	def relative_paths(self) -> bool:
		return self._session_path.uses_relative
	@relative_paths.setter
	def relative_paths(self, value):
		self._session_path = SessionLocationBlock(self._session_path.session_path, value)

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

	def __on_saved__(self, output_dir : str): 
		if not self._session_path.uses_relative:
			return
		self.included_files = self.included_files.make_relative(output_dir)
		
	@abstractmethod
	def __item_added__(self, added : Sequence[FileInfo]): 
		raise NotImplementedError()
	@abstractmethod
	def __item_removed__(self, removed : Sequence[FileInfo]): 
		raise NotImplementedError()
	
	@classmethod
	def __import__(cls, attributes: AttrDict, **cls_kw) -> Self:
		block = attributes['location_info']
		session= cls(attributes['name'], block.session_path, force_validation= attributes['force_validation'], 
					use_relativePaths= block.uses_relative, **cls_kw)
		session.archetype = attributes['archetype']
		session.included_files = attributes['included_files']
		session.included_stars = attributes['included_stars']
		RelativeContext.reset()
		return session
	
	def __export__(self) -> AttrDict:
		return {
			'name': self.name, 
			'location_info' : self._session_path,
			'archetype' : self.archetype,
			'included_files': self.included_files, 
			'included_stars': self.included_stars, 
			'force_validation' : self.force_validation}
	
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
	