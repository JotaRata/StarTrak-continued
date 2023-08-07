from ast import literal_eval
from typing import Iterable, Iterator
from startrak.types import FileInfo
from startrak.types import Star
from os import  scandir

__all__ = ['load_file', 'load_folder', 'export_stars', 'import_stars']
# ----- Wrapper functions around astropy.io --------
def load_file(path: str) -> FileInfo:
    return FileInfo(path)

def retrieve_data(fileInfo : FileInfo):
    return fileInfo.get_data()

def load_folder(dir: str, *args, **kwargs):
    for entry in os.scandir(dir):
        if not entry.is_file() and not entry.name.endswith(
            ('.fit', '.fits', '.FIT', '.FITS')):
            continue
        yield load_file(entry.path)
