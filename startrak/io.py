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

def load_folder(dir: str):
    for entry in scandir(dir):
        if not entry.is_file() and not entry.name.endswith(
            ('.fit', '.fits', '.FIT', '.FITS')):
            continue
        yield load_file(entry.path)

def export_stars(path : str, star_collection : Iterable[Star]):
    with open(path + '.stlist', 'w') as out:
        out.write('# Exported from Startrak\n')
        out.write('# Type\tName\tPosition\tRadius\tExtra\n')
        for star in star_collection:
            line = '\t'.join(map(str, star.export()))
            out.write(line + '\n')

def import_stars(path : str) -> Iterator[Star]:
    assert path.endswith(('.stlist', '.list', 'txt')), 'Not a text file'
    with open(path, 'r') as file:
        for line in file:
            if line.lstrip().startswith('#'): continue
            _type, _name, _pos, _rad, *_extras = line.split('\t')

            T = globals().get(_type, None)
            assert issubclass(T, Star), f'Type "{T}" is not a subclass of Star'
            _args = [literal_eval(arg) for arg in _extras]
            _pos = literal_eval(_pos)
            star = T(_name, tuple(_pos), int(_rad), *_args)
            yield star