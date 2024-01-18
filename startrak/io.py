from functools import cache
from pathlib import Path
from startrak.native import FileInfo, FileList
from os import  scandir

from startrak.sessionutils import get_session

__all__ = ['load_file', 'load_folder', 'retrieve_data', 'clear_cache']

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

def retrieve_data(fileInfo : FileInfo):
    return fileInfo.get_data()

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