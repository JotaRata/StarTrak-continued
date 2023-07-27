from startrak.utils import extension_method
from enum import StrEnum
from startrak.internals.types import Session
from startrak.internals.types import InspectionSession as _inspect
from startrak.internals.types import ScanSession as _scan


class SessionType(StrEnum):
		ASTRO_INSPECT = 'inspect'
		ASTRO_SCAN = 'scan'
		
@extension_method(Session, static=True, name= 'Create')
def create_session(sessionType : SessionType, name : str, *args, **kwargs) -> Session:
		'''
			Extesion factory method to create sessions using the SessionType enum
			Parameters:
			- sessionType (SessionType): The type of the new session. Accepted values are:
				- - SessionType.ASTRO_INSPECT ('inspect') = Analyze already saved files in the disk
				- - SessionType.ASTRO_SCAN ('scan') = Load and Analyze files as they are being created in a folder

			- name (str): Name of the new session.
		'''
		session : Session = None
		if sessionType == SessionType.ASTRO_INSPECT:
				session = object.__new__(_inspect).__post_init__()
		elif sessionType == SessionType.ASTRO_SCAN:
				session = object.__new__(_scan).__post_init__()
		else: raise TypeError('Invalid case')

		Session.currentSession = session
		return session._create(name, *args, **kwargs)

def get_session() -> Session:
	'''Returns the current session'''
	return Session.currentSession