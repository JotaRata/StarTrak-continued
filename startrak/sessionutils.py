from enum import StrEnum
from startrak.types.sessions import *

__all__ = ['new_session', 'get_session', 'SessionType']
__session__ : Session | None = None
SessionType = StrEnum('SessionType', {'ASTRO_INSPECT': 'inspect','ASTRO_SCAN' : 'scan'})

def new_session(sessionType : SessionType, name : str, *args, **kwargs) -> Session:
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

def get_session() -> Session | None:
	'''Returns the current session'''
	return __session__