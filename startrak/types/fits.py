from io import BufferedReader
from typing import Iterator, Union, Tuple

_ValueType = Union[int, float, str, bool]
def _parse_header(_file : BufferedReader) -> Iterator[Tuple[str, _ValueType]]:
	while True:
		line = _file.read(80)
		if not line: break
		if b'END' in line: break
		_validate_line(line)
		_keyword = line[:8].decode().rstrip()
		_value = _parse_value(line)
		yield _keyword, _value
      
def _parse_value(src : bytes) -> _ValueType:
	if src[10] == 39:
		end = src.rfind(39, 19)
		return src[11:end].decode()
	if src[29] == 84 or src[29] == 66:
		return src[29] == 84
	line = src[10:30].decode()
	num = float(line)
	if num.is_integer():
		return int(num)
	return num


def _validate_line(line : bytes):
	if not (line[8] == 61 and line[9] == 32):
		raise IOError('Invalid header syntax')
   
f = open('tests/sample_files/aefor4.fit', 'rb')
g = _parse_header(f)

next(g)

ord('T')
ord('B')
ord("'")