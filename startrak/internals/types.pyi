# Stubs file for ./types.pyx
from datetime import datetime
from typing import Any, Callable, Literal
from astropy.io import fits

from startrak.sessions import SessionType

class FileInfo():
		path : str
		size : int
		header : Header
		
		@staticmethod
		def fromHDU(hdu: fits.HDUList) -> FileInfo: ...

class Header():
	'''Lightweight version of an astropy header'''
	def __init__(self, source : fits.Header | dict): ...

class HeaderArchetype(Header):
	def validate(self, header : Header, failed : Callable[[str, Any, Any]] = None) -> bool: ...

class Session():
		currentSession : Session

		name : str
		working_dir : str
		tracked_items : set[FileInfo]
		archetype : HeaderArchetype
		creation_time : datetime

		def __post_init__(self): ...

		def add_item(self, item : Any | list): ...
		def remove_item(self, item : Any | list): ...
		
		@staticmethod
		def Create(sessionType : SessionType | Literal['inspect', 'scan'], name : str, *args, **kwargs) -> Session: ...
		def _create(self, name, *args, **kwargs) -> Session: ...
		def save(self, out): ...

class InspectionSession(Session): ...
class ScanSession(Session): ...