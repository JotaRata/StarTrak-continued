from enum import StrEnum
from typing import Literal, Optional, overload
from startrak.native import Session
from startrak.types.sessions import *

__all__ = ['new_session', 'get_session', 'SessionType']
SessionType = Literal['inspect', 'scan']
__session__ : Session = InspectionSession('default')

@overload
def new_session(name : str, sessionType : Literal['inspect'], *args, forced : bool = False, **kwargs) -> InspectionSession: ...
@overload
def new_session(name : str, sessionType : Literal['scan'], *args, forced : bool = False, **kwargs) -> ScanSession: ...

def new_session(name : str, sessionType : SessionType = 'inspect', *args, forced : bool = False, **kwargs) -> Session:
	'''
		Creates a new session of the specified type, if another session exists a RuntimeError will be raised unless the forced flag is enabled.

		Parameters:
		* name (str): The name of the new session
		* sessionType ("inspect" or "scan"): The type of the new session. Default: "inspect".
			* "inspect" will create a emtpy session useful to work with files already saved in disk.
			* "scan" will actively scan in a given directory if new files were added or removed, useful for real-time analysis. 
		* *args: Additional arguments for the newly created Session, if sessionType = "scan" then the working directory must be specified here or in **kwargs.
		* forced (bool): Whether the new session should overwrite the previous one if exists, if False then a RunTimeError is raised upon calling this function if another session already exists. Default: False.
		* **kwargs: Additional keywords for the newly created session.

		Returns:
		* InspectionSession if sessionType = "inspect"
		* ScanSession if sessionType = "scan"
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