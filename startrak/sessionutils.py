from pathlib import Path
from typing import Collection, Literal, overload
from startrak.native import FileList, Session, Star
from startrak.native.classes import RelativeContext
from startrak.types.sessions import *
from startrak.types.exporters import TextExporter
from startrak.types.importers import TextImporter

__all__ = ['new_session', 'get_session', 'save_session', 'SessionType']
SessionType = Literal['inspect', 'scan']
__session__ : Session = InspectionSession('default')

@overload
def new_session(name : str, sessionType : Literal['inspect'], *args, overwrite : bool = False, **kwargs) -> InspectionSession: ...
@overload
def new_session(name : str, sessionType : Literal['scan'], *args, overwrite : bool = False, **kwargs) -> ScanSession: ...

def new_session(name : str, sessionType : SessionType = 'inspect', *args, overwrite : bool = False, **kwargs) -> Session:
	'''
		Creates a new session of the specified type, if another session exists a RuntimeError will be raised unless the overwrite flag is enabled.

		Parameters:
		* name (str): The name of the new session
		* sessionType ("inspect" or "scan"): The type of the new session. Default: "inspect".
			* "inspect" will create a emtpy session useful to work with files already saved in disk.
			* "scan" will actively scan in a given directory if new files were added or removed, useful for real-time analysis. 
		* *args: Additional arguments for the newly created Session, if sessionType = "scan" then the working directory must be specified here or in **kwargs.
		* overwrite (bool): Whether the new session should overwrite the previous one if exists, if False then a RunTimeError is raised upon calling this function if another session already exists. Default: False.
		* **kwargs: Additional keywords for the newly created session.

		Returns:
		* InspectionSession if sessionType = "inspect"
		* ScanSession if sessionType = "scan"
	'''
	global __session__
	if (__session__ and __session__.name != 'default') and not overwrite:
		raise RuntimeError(f'A Session of type {type(__session__).__name__} already exists, to overwrite call this function again with overwrite= True')

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

def load_session(file_path : str | Path, overwrite : bool = True) -> Session:
	''' Loads a session from disk and returns it, if overwrite is True then the current session is set to the loaded one'''
	global __session__
	extension = '' if str(file_path).endswith('.trak') else '.trak'
	with TextImporter(str(file_path) + extension) as f:
		obj = f.read()
	if not isinstance(obj, Session):
		raise TypeError('Read object is not of type Session.')
	
	if overwrite:
		__session__ = obj
	return obj

def save_session(output_path : str | Path):
	''' Saves the current session to the specified path'''
	extension = '' if str(output_path).endswith('.trak') else '.trak'
	with TextExporter(str(output_path) + extension) as out:
		directory = os.path.abspath(os.path.join(output_path, os.pardir)).replace('\\', '/') 
		__session__.__on_saved__( directory )
		
		with RelativeContext(__session__.working_dir):
			out.write(__session__)

# Wrapper functions around current session methods
def add_file(file : FileInfo | Collection[FileInfo]):
	''' Adds a file or list of files to the current session '''
	if type(file) is FileInfo:
		__session__.add_file(file)
	else:
		__session__.add_file(**file)

def remove_file(file : FileInfo | Collection[FileInfo] | str):
	''' Removes a file or list of files to the current session'''
	if type(file) is FileInfo:
		__session__.remove_file(file)
	elif type(file) is str:
		_file = __session__.included_files[file]
		__session__.remove_file(_file)
	else:
		__session__.remove_file(**file)

def add_star(star : Star | Collection[Star]):
	''' Adds a star or list of stars to the current session '''
	if type(star) is Star:
		__session__.add_star(star)
	else:
		__session__.add_star(**star)

def remove_star(star : Star | Collection[Star] | str):
	''' Removes a star or list of stars to the current session '''
	if type(star) is Star:
		__session__.remove_star(star)
	elif type(star) is str:
		_star = __session__.included_stars[star]
		__session__.remove_star(_star)
	else:
		__session__.remove_star(**star)
