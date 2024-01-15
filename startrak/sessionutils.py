from enum import StrEnum
from typing import Literal, Optional
from startrak.native import Session
from startrak.types.sessions import *

__all__ = ['new_session', 'get_session', 'SessionType']
SessionType = Literal['inspect', 'scan']
__session__ : Session = InspectionSession('default')

def new_session(name : str, sessionType : SessionType = 'inspect', *args, forced : bool = False, **kwargs) -> Session:
	'''
		Parameters:
		- sessionType (SessionType): The type of the new session. Accepted values are:
			- - SessionType.ASTRO_INSPECT ('inspect') = Analyze already saved files in the disk
			- - SessionType.ASTRO_SCAN ('scan') = Load and Analyze files as they are being created in a folder

		- name (str): Name of the new session.
	'''
	global __session__
	if (__session__ and __session__.name != 'default') and not forced:
		raise RuntimeError(f'A Session of type {type(__session__).__name__} already exists, to overwrite call this function again with forced= True')

	session : Session
	match sessionType:
		case 'inspect':
			session = InspectionSession(name, *args, **kwargs)
		case 'scan':
			session = ScanSession(name, *args, **kwargs)
		case _:
			raise NameError(f'Invalid session type: "{sessionType}", expected "inspect" or "scan".')	

	__session__ = session
	return session

def get_session() -> Session:
	'''Returns the current session'''
	return __session__