from .types.sessions import SessionType
from .types.sessions import Session as _Session
from .types.sessions import InspectionSession as _InspectionSession
from .types.sessions import ScanSession as _ScanSession
from .io import *

APPNAME = "StarTrak"
VERSION = "1.0.0"

__session__ : _Session = None

def new_session(sessionType : SessionType, name : str, *args, **kwargs) -> _Session:
	'''
		Parameters:
		- sessionType (SessionType): The type of the new session. Accepted values are:
			- - SessionType.ASTRO_INSPECT ('inspect') = Analyze already saved files in the disk
			- - SessionType.ASTRO_SCAN ('scan') = Load and Analyze files as they are being created in a folder

		- name (str): Name of the new session.
	'''
	session : _Session
	if sessionType == SessionType.ASTRO_INSPECT:
			session = _InspectionSession(name, *args, **kwargs)
	elif sessionType == SessionType.ASTRO_SCAN:
			session = _ScanSession(name, *args, **kwargs)
	else: raise TypeError('Invalid case')

	global __session__
	__session__ = session
	return session

def get_session() -> _Session:
	'''Returns the current session'''
	return __session__