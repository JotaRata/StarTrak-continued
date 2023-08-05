import os
import numpy as np
from startrak.types import FileInfo


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
