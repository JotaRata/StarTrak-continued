import astropy.io

from .types.sessions import InspectionSession, ScanSession, Session, SessionType
from .internals import types
from . import io

APPNAME = "StarTrak"
VERSION = "1.0.0"

__session__ : Session = None

def create_session(sessionType : SessionType, name : str, *args, **kwargs) -> Session:
	'''
		Parameters:
		- sessionType (SessionType): The type of the new session. Accepted values are:
			- - SessionType.ASTRO_INSPECT ('inspect') = Analyze already saved files in the disk
			- - SessionType.ASTRO_SCAN ('scan') = Load and Analyze files as they are being created in a folder

		- name (str): Name of the new session.
	'''
	session : Session
	if sessionType == SessionType.ASTRO_INSPECT:
			session = InspectionSession(name, *args, **kwargs)
	elif sessionType == SessionType.ASTRO_SCAN:
			session = ScanSession(name, *args, **kwargs)
	else: raise TypeError('Invalid case')

	global __session__
	__session__ = session
	return session

def get_session() -> Session:
	'''Returns the current session'''
	return __session__