from functools import cache
from pathlib import Path
from startrak.native import FileInfo, FileList
from os import  scandir

from startrak.sessionutils import get_session

__all__ = ['load_file', 'load_folder', 'get_data', 'clear_cache']

@cache
def load_file(path: str | Path, append : bool = True) -> FileInfo:
    '''
        Loads a FITS file.
        path (str | Path): The path of the file to load
        append (bool): If True, append the file to the current session, default: True
    '''
    file = FileInfo.new(str(path))
    if append and file:
        get_session().add_file(file)
    return file

def get_data(file_name_or_idx : FileInfo | str | int):
    ''' Retrieves the data from the specified file, this can be provided as the name of the file in the current session or its positional index, as well as just giving the FileInfo object directly.'''
    if isinstance(file_name_or_idx, (str, int)):
        fileinfo = get_session().included_files[file_name_or_idx]
    else:
        fileinfo = file_name_or_idx
    return fileinfo.get_data()

def load_folder(path: str | Path, append : bool = True):
    '''
        Loads a folder containing FITS files.
        path (str | Path): The path of the folder to load
        append (bool): If True, append the file to the current session, default: True
    '''
    files = []
    for entry in scandir(path):
        if not entry.is_file() or not entry.name.endswith(
            ('.fit', '.fits', '.FIT', '.FITS')):
            continue
        file = FileInfo.new(str(entry.path))
        files.append(file)
    if append:
        get_session().add_file( *files)
    return FileList( *files)

def clear_cache():
    load_file.cache_clear()