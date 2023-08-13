from abc import ABC, abstractmethod
from typing import List, Optional, Set
from startrak.types import FileInfo, HeaderArchetype, Header

class Session(ABC):
	name : str
	archetype : Optional[HeaderArchetype]
	included_items : Set[FileInfo]
	
	def __init__(self, name : str):
		self.name = name
		self.archetype : HeaderArchetype = None
		self.included_items : set[FileInfo] = set()
	
	def __repr__(self) -> str:
				return ( f'{type(self).__name__} : "{self.name}"\x7f\n'
							f'Included : {self.included_items}\n')

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
	def __item_added__(self, added : Set[FileInfo]): pass
	@abstractmethod
	def __item_removed__(self, removed : Set[FileInfo]): pass
	@abstractmethod
	def save(self, out : str): pass

class InspectionSession(Session):
	def __item_added__(self, added : Set[FileInfo]): pass
	def __item_removed__(self, removed : Set[FileInfo]): pass

	def save(self, out : str):
		pass    # todo: Add logic for saving sessions

class ScanSession(Session):
	working_dir : str
	def __init__(self, name: str, scan_dir : str):
		super().__init__(name)
		self.working_dir = scan_dir

	def __item_added__(self, added : Set[FileInfo]): pass
	def __item_removed__(self, removed : Set[FileInfo]): pass

	def __repr__(self) -> str:
		return super().__repr__().replace('\x7f\n',
		f'\nDirectory: {self.working_dir}\n')
	def save(self, out : str):
		pass
