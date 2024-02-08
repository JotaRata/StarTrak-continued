# compiled module

from __future__ import annotations
import os
from typing import Dict, Iterable, List, Self, overload
from startrak.native.classes import FileInfo, RelativeContext
from startrak.native.alias import MaskLike
from startrak.native.ext import STCollection

class FileList(STCollection[FileInfo]):
	_dict : Dict[str, int]
	def __init__(self, *values: FileInfo):
		oset = dict.fromkeys(values).keys()
		super().__init__(*oset)

	def __post_init__(self):
		self._dict = {s.name : i for i, s in enumerate(self._internal)}
	
	@property
	def paths(self) -> List[str]:
		return [f.path for f in self._internal]
	@property
	def names(self) -> List[str]:
		return [f.name for f in self._internal]
	
	def make_relative(self, relative_path : str) -> FileList:
		with RelativeContext(relative_path):
			files = [FileInfo.new(file.path, True) for file in self]
		return FileList( *files)
	
	def make_abslute(self, relative_path : str) -> FileList:
		files = [FileInfo.new(os.path.join(relative_path, file.path), False) for file in self]
		return FileList( *files)
		
	def append(self, value: FileInfo):
		if value not in self:
			super().append(value)
	def insert(self, index: int, value: FileInfo):
		if value not in self:
			super().insert(index, value)
	def extend(self, values: Self | Iterable[FileInfo]):
		return super().extend([ v for v in values if v not in self])
	
	def __setitem__(self, index: int, value: FileInfo):
		raise TypeError('Cannot directly modify FileList')
	def __contains__(self, item : FileInfo | str): #type: ignore[override]
		if isinstance(item, str):
			return item in self._dict
		return item.name in self._dict

	@overload
	def __getitem__(self, index: int | str, /) -> FileInfo: ...
	@overload
	def __getitem__(self, index: slice | MaskLike, /) -> FileList: ...
	def __getitem__(self, index : int | slice  | MaskLike | str) -> FileInfo | FileList:
		if type(index) is str:
			idx = self._dict[index]
			return self._internal[idx]
		else:
			assert not isinstance(index, str)
		return super().__getitem__(index)

	def __on_change__(self):
		super().__on_change__()
		self._dict = {s.name : i for i, s in enumerate(self._internal)}