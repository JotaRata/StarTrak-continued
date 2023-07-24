import os
import numpy as np
from astropy.io import fits
from startrak.types import FileInfo


# ----- Wrapper functions around astropy.io --------
def load_file(path: str, *args, **kwargs) -> FileInfo:
    with fits.open(path, *args, **kwargs) as hdu:
        return FileInfo.fromHDU(hdu)

def retrieve_data(fileInfo : FileInfo):
    return fits.getdata(fileInfo.path)

def load_folder(dir: str, *args, **kwargs):
    for entry in os.scandir(dir):
        if not entry.is_file() and not entry.name.endswith(
            ('.fit', '.fits', '.FIT', '.FITS')):
            continue
        yield load_file(entry.path)
