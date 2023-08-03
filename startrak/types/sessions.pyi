# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\types\sessions.pyx"

from startrak.types.abstract import Interface
from startrak.types.abstract import abstract
from enum import StrEnum

class SessionType(StrEnum):
	ASTRO_INSPECT = 'inspect'
	ASTRO_SCAN = 'scan'
	
class Session(Interface):
	def __init__(self, name : str, *args, **kwargs): ...
		# todo: raise warning if no items were added
	def save(self, out): ...

class InspectionSession(Session):
	def save(self, out : str): ...

class ScanSession(Session):
	def __init__(self, name: str, scan_dir : str): ...
	def save(self, out): ...
