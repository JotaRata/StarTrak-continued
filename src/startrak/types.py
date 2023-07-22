import os
from enum import Enum
from dataclasses import dataclass
from astropy.io import fits


class SessionType(Enum):
    ASTRO_SCAN = 1
    ASTRO_INSPECT = 2


@dataclass(frozen=True)
class FileInfo():
    path: str
    size: int
    validated: bool
    headers: list[fits.Header]

    def FromHDU(hdu_list: fits.HDUList):
        path = hdu_list.filename()
        sbytes = os.path.getsize(path)
        ver = hdu_list.verify('fix')
        headers = [hdu.header for hdu in hdu_list]

        return FileInfo(path, sbytes, ver, headers)
