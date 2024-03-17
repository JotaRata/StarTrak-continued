from pathlib import Path
from typing import Collection, Literal, overload
from startrak.native import FileList, Session, Star, StarList
from startrak.native.classes import RelativeContext
from startrak.types.sessions import *
from startrak.types.exporters import TextExporter
from startrak.types.importers import TextImporter

__all__ = ['new_session', 
				'load_session', 
				'get_session', 
				'load_session',
				'save_session', 
				'SessionType',
				'add_file',
				'remove_file',
				'add_star',
				'remove_star',
				'get_file',
				'get_star',
				'get_files',
				'get_stars',]
SessionType = Literal['inspect', 'scan']

if not os.environ.get('ST_SESSION_DISABLED', None):
	__session__ : Session = InspectionSession('default')
else:
	__session__ = None

@overload
def new_session(name : str, sessionType : Literal['inspect'], *args, overwrite : bool, **kwargs) -> InspectionSession: ...
@overload
def new_session(name : str, sessionType : Literal['scan'], *args, overwrite : bool, **kwargs) -> ScanSession: ...

def new_session(name : str, sessionType : SessionType = 'inspect', *args, overwrite : bool = True, **kwargs) -> Session:
	'''
		Creates a new session of the specified type and returns it.

		Parameters:
		* name (str): The name of the new session
		* sessionType ("inspect" or "scan"): The type of the new session. Default: "inspect".
			* "inspect" will create a emtpy session useful to work with files already saved in disk.
			* "scan" will actively scan in a given directory if new files were added or removed, useful for real-time analysis. 
		* *args: Additional arguments for the newly created Session, if sessionType = "scan" then the working directory must be specified here or in **kwargs.
		* overwrite (bool): Whether the new session should overwrite the previous one if exists Default: False.
		* **kwargs: Additional keywords for the newly created session.

		Returns:
		* InspectionSession if sessionType = "inspect"
		* ScanSession if sessionType = "scan"
	'''
	global __session__
	session : Session
	match sessionType:
		case 'inspect':
			session = InspectionSession(name, *args, **kwargs)
		case 'scan':
			session = ScanSession(name, *args, **kwargs)
		case _:
			raise NameError(f'Invalid session type: "{sessionType}", expected "inspect" or "scan".')	
	
	if overwrite:
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
	elif isinstance(file, Collection):
		__session__.add_file( *file)
	else:
		raise TypeError(type(file))

def remove_file(file : FileInfo | Collection[FileInfo] | str):
	''' Removes a file or list of files to the current session'''
	if type(file) is FileInfo:
		__session__.remove_file(file)
	elif type(file) is str:
		_file = __session__.included_files[file]
		__session__.remove_file(_file)
	elif isinstance(file, Collection):
		__session__.remove_file( *file)
	else:
		raise TypeError(type(file))

def add_star(star : Star | Collection[Star]):
	''' Adds a star or list of stars to the current session '''
	if type(star) is Star:
		__session__.add_star(star)
	elif isinstance(star, Collection):
		__session__.add_star( *star)
	else:
		raise TypeError(type(star))

def remove_star(star : Star | Collection[Star] | str):
	''' Removes a star or list of stars to the current session '''
	if type(star) is Star:
		__session__.remove_star(star)
	elif type(star) is str:
		_star = __session__.included_stars[star]
		__session__.remove_star(_star)
	elif isinstance(star, Collection):
		__session__.remove_star( *star)
	else:
		raise TypeError(type(star))

def get_file(name_or_index : str | int) -> FileInfo:
	''' Returns a single file in the current session based on the provided name or positional index'''
	return __session__.included_files[name_or_index]

def get_star(name_or_index : str | int) -> Star:
	''' Returns a single star in the current session based on the provided name or positional index'''
	return __session__.included_stars[name_or_index]

def get_files() -> FileList:
	''' Returns a read-only copy of the current session included files list'''
	return __session__.included_files.copy(closed= True)

def get_stars() -> StarList:
	''' Returns a read-only copy of the current session included stars list'''
	return __session__.included_stars.copy(closed= True)