# compiled module

from __future__ import annotations
from typing import Dict, List, overload
from startrak.native.classes import FileInfo
from startrak.native.alias import MaskLike
from startrak.native.ext import STCollection

class FileList(STCollection[FileInfo]):
	_dict : Dict[str, int]
	def __post_init__(self):
		self._dict = {s.name : i for i, s in enumerate(self._internal)}
	
	@property
	def paths(self) -> List[str]:
		return [f.path for f in self._internal]

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