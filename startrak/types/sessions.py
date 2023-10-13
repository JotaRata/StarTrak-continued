from abc import ABC, abstractmethod
from typing import List, Optional, Set
from startrak.native import FileInfo, HeaderArchetype, Header, Session

class InspectionSession(Session):
	def __item_added__(self, added : Set[FileInfo]): pass
	def __item_removed__(self, removed : Set[FileInfo]): pass

	def save(self, out : str):
		pass    # todo: Add logic for saving sessions

class ScanSession(Session):
	working_dir : str
	def __init__(self, name: str, scan_dir : str):
		super().__init__(name)
		self.working_dir = scan_dir

	def __item_added__(self, added : Set[FileInfo]): pass
	def __item_removed__(self, removed : Set[FileInfo]): pass

	def __repr__(self) -> str:
		return super().__repr__().replace('\x7f\n',
		f'\nDirectory: {self.working_dir}\n')
	def save(self, out : str):
		pass
