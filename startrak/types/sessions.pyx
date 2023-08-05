from startrak.types cimport FileInfo, HeaderArchetype, Header
from startrak.types.abstract cimport Interface
from startrak.types.abstract import abstract
from enum import StrEnum

ctypedef fused _FileOrList:
	FileInfo
	list

class SessionType(StrEnum):
		ASTRO_INSPECT = 'inspect'
		ASTRO_SCAN = 'scan'

cdef class Session(Interface):
	def __init__(self, str name, *args, **kwargs):
		self.name = name
		self.working_dir : str = str()
		self.archetype : HeaderArchetype = None
		self.included_items : set[FileInfo] = set()
	
	def __repr__(self) -> str:
				return ( f'{type(self).__name__} : "{self.name}"\n'
							f'Directory: {self.working_dir}\n'
							f'Included : {self.included_items}\n')

	def add_item(self, _FileOrList item): 
		_items = item if type(item) is list else [item]
		_added = {_item for _item in _items if type(_item) is FileInfo}
		if len(self.included_items) == 0:
			first = next(iter(_added))
			assert isinstance(first, FileInfo)
			self.set_archetype(first.header)
		
		self.included_items |= _added
		self.__item_added__(_added)
		# todo: raise warning if no items were added

	def remove_item(self, _FileOrList item): 
		_items = item if type(item) is list else [item]
		_removed = {_item for _item in _items if type(_item) is FileInfo}
		self.included_items -= _removed
		self.__item_removed__(_removed)
	
	def set_archetype(self, Header header):
		if header is None: self.archetype = None
		self.archetype = HeaderArchetype(header)

	@abstract
	def __item_added__(self, added): pass
	@abstract
	def __item_removed__(self, removed): pass
	@abstract 
	def save(self, out): pass

class InspectionSession(Session):
	def __item_added__(self, added): pass
	def __item_removed__(self, removed): pass

	def save(self, out : str):
		pass    # todo: Add logic for saving sessions

class ScanSession(Session):
	def __init__(self, name: str, scan_dir : str):
		super().__init__(name)
		self.working_dir = scan_dir

	def __item_added__(self, added): pass
	def __item_removed__(self, removed): pass

	def save(self, out):
		pass
