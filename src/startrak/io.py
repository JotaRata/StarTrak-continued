import os
import numpy as np
from astropy.io import fits
from startrak.types import FileInfo


def load_file(path: str, *args, **kwargs) -> FileInfo:
    with fits.open(path, *args, **kwargs) as hdu:
        return FileInfo.FromHDU(hdu)
