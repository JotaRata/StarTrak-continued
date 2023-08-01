from startrak.internals.exceptions import InstantiationError
from startrak.internals.types import FileInfo, HeaderArchetype, Header
from abc import ABC, abstractmethod
from typing import Any
import datetime


class Session(ABC):
    currentSession : Session 	# todo: move somewhere else
    
    #@self.name = 'New Session'
    #@self.working_dir : str 
    #@self.archetype : HeaderArchetype 
    #@self.tracked_items : set[FileInfo]
    #@self.creation_time = datetime.now()
    
    def __init__(self):
        raise InstantiationError(self, 'Session.Create')

    def __repr__(self) -> str:
        return f'{type(self).__name__}: ' + str(", ".join(
            [f'{k} = {v}' for k, v in self.__dict__.items()]))
    
    def __post_init__(self):
        self.name = 'New Session'
        self.working_dir : str = str()
        self.archetype : HeaderArchetype = None
        self.tracked_items : set[FileInfo] = set()
        self.creation_time = datetime.now()
        return self

    def add_item(self, item : Any | list): 
        _items = item if type(item) is list else [item]
        _added = {_item for _item in _items if type(_item) is FileInfo}
        if len(self.tracked_items) == 0:
            first = next(iter(_added))
            assert isinstance(first, FileInfo)
            self.set_archetype(first.header)
        
        self.tracked_items |= _added
        self.__item_added__(_added)
        # todo: raise warning if no items were added

    def remove_item(self, item : Any | list): 
        _items = item if type(item) is list else [item]
        _removed = {_item for _item in _items if type(_item) is FileInfo}
        self.tracked_items -= _removed
        self.__item_removed__(_removed)
    
    def set_archetype(self, header : Header):
        if header is None: self.archetype = None
        self.archetype = HeaderArchetype(header)
    @abstractmethod
    def _create(self, name, *args, **kwargs) -> Session: pass
    @abstractmethod
    def __item_added__(self, added): pass
    @abstractmethod
    def __item_removed__(self, removed): pass
    @abstractmethod 
    def save(self, out): pass
