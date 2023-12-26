# compiled module

from __future__ import annotations

from typing import Dict, overload
from startrak.native.classes import Star
from startrak.native.alias import MaskLike
from startrak.native.collections.position import PositionArray
from startrak.native.ext import STCollection

class StarList(STCollection[Star]):
	_dict : Dict[str, int]
	def __post_init__(self):
		self._dict = {s.name : i for i, s in enumerate(self._internal)}
	
	@property
	def positions(self) -> PositionArray:
		return PositionArray( *(s.position for s in self._internal))
	
	def to_dict(self) -> Dict[str, Star]:
		return {s.name : s for s in self._internal}

	@overload
	def __getitem__(self, index: int | str, /) -> Star: ...
	@overload
	def __getitem__(self, index: slice | MaskLike, /) -> StarList: ...
	def __getitem__(self, index : int | slice  | MaskLike | str) -> Star | StarList:
		if type(index) is str:
			idx = self._dict[index]
			return self._internal[idx]
		else:
			assert not isinstance(index, str)
		return super().__getitem__(index)

	def __on_change__(self):
		super().__on_change__()
		self._dict = {s.name : i for i, s in enumerate(self._internal)}