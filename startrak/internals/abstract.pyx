from startrak.exceptions import *
from startrak.internals.types cimport FileInfo, HeaderArchetype, Header

ctypedef fused _FileOrList:
	FileInfo
	list

cdef class Interface:
	def __cinit__(self):
		_type = type(self)
		if _type.__base__ is Interface or _type is Interface:
			raise InstantiationError(self)
		
def abstract(func):
	def wrapper(*args, **kwargs):  # stub: ignore
		raise NotImplementedError(func.__name__)
	return wrapper

# -------------- Classes -------------------

cdef class Session(Interface):
		currentSession : Session 	# todo: move somewhere else
		cdef public str name
		cdef public str working_dir
		cdef readonly HeaderArchetype archetype
		cdef readonly set[FileInfo] included_files

		def __repr__(self) -> str:
				return f''' {type(self).__name__} : "{self.name}" 
				Working directory: {self.working_dir}.
				Included files: {self.included_files}'''
		
		def __post_init__(self):
				self.name = 'New Session'
				self.working_dir = str()
				self.archetype = None
				self.included_files  = set()
				# self.creation_time = datetime.now()
				return self

		def add_item(self, _FileOrList item): 
				_items = item if type(item) is list else [item]
				_added = {_item for _item in _items if type(_item) is FileInfo}
				if len(self.included_files) == 0:
						first = next(iter(_added))
						assert isinstance(first, FileInfo)
						self.set_archetype(first.header)
				
				self.included_files |= _added
				self.__item_added__(_added)
				# todo: raise warning if no items were added

		def remove_item(self, _FileOrList item): 
				_items = item if type(item) is list else [item]
				_removed = {_item for _item in _items if type(_item) is FileInfo}
				self.included_files -= _removed
				self.__item_removed__(_removed)
		
		def set_archetype(self, Header header):
				if header is None: self.archetype = None
				self.archetype = HeaderArchetype(header)
		@abstract
		def _create(self, str name, *args, **kwargs) -> Session: pass
		@abstract
		def __item_added__(self, added): pass
		@abstract
		def __item_removed__(self, removed): pass
		@abstract 
		def save(self, out): pass
