# Stubs file for ./types.pyx
from datetime import datetime
from typing import Any, Literal
from astropy.io.fits import HDUList

from startrak.sessions import SessionType

class FileInfo():
		path : str
		size : int
		header : dict[str, str]
		
		@staticmethod
		def fromHDU(hdu: HDUList) -> FileInfo: ...

class Session():
		currentSession : Session

		name : str
		working_dir : str
		tracked_items : set[FileInfo]
		file_arch : Any
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