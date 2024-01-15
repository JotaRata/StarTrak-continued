from pathlib import Path
from startrak.native import FileInfo, FileList
from os import  scandir

from startrak.sessionutils import get_session

__all__ = ['load_file', 'load_folder']
# ----- Wrapper functions around astropy.io --------
def load_file(path: str | Path, append : bool = True) -> FileInfo:
    '''
        Loads a FITS file.
        path (str | Path): The path of the file to load
        append (bool): If True, append the file to the current session, default: True
    '''
    file = FileInfo(str(path))
    if append:
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
        if not entry.is_file() and not entry.name.endswith(
            ('.fit', '.fits', '.FIT', '.FITS')):
            continue
        files.append(load_file(entry.path, append))
    return FileList( *files)
