from startrak.internals.types import Session, InspectionSession, ScanSession
from startrak.utils import extension_method
from enum import StrEnum


class SessionType(StrEnum):
		ASTRO_INSPECT = 'inspect'
		ASTRO_SCAN = 'scan'
		
@extension_method(Session, static=True)
def Create(sessionType : SessionType, name : str, *args, **kwargs):
		'''
			Extesion factory method to create sessions using the SessionType enum
			Parameters:
			- sessionType (SessionType): The type of the new session. Accepted values are:
				- - SessionType.ASTRO_INSPECT = Analyze already saved files in the disk
				- - SessionType.ASTRO_SCAN = Load and Analyze files as they are being created in a folder

			- name (str): Name of the new session.
		'''
		session : Session = None
		if sessionType == SessionType.ASTRO_INSPECT:
				session = object.__new__(InspectionSession).__post_init__()
		elif sessionType == SessionType.ASTRO_SCAN:
				session = object.__new__(ScanSession).__post_init__()
		else: raise TypeError('Invalid case')

		return session._create(name, *args, **kwargs)
