from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping
import os
from threading import Thread
import time
from typing import Any, Self, Sequence, Set
from startrak.native import FileInfo, Session
from startrak.native.classes import FileInfo
from startrak.native.ext import AttrDict

class InspectionSession(Session):
	def __init__(self, name: str, working_dir: str | None = ''):
		super().__init__(name, working_dir if working_dir else os.getcwd())

	def __item_added__(self, added : Sequence[FileInfo]): pass
	def __item_removed__(self, removed : Sequence[FileInfo]): pass
	

class ScanSession(Session):
	_watcher : DirectoryWatcher | None
	class DirectoryWatcher(Thread):
		def __init__(self, session : ScanSession, cadence_ms : int = 100, *args) -> None:
			super().__init__(name= 'watcher-thread', daemon=False)
			self._session = session
			self._sleep = cadence_ms / 1000
			self._stop = False
		def start(self) -> None:
			self._stop = False
			return super().start()
		def stop(self) -> None:
			self._stop = True
		
		def run(self):
			before = self._session.included_files.names
			while not self._stop:
				time.sleep (self._sleep)
				after = os.listdir (self._session.working_dir)
				added = [f for f in after if not f in before]
				removed = [f for f in before if not f in after]
				if added:
					self.process_added(added)
				if removed: 
					self.process_removed(removed)
				before = after

		def process_added(self, names : list[str]):
			files = []
			for name in names:
				path = os.path.join(self._session.working_dir, name)
				if os.path.isfile(path) and not name.endswith(
					('.fit', '.fits', '.FIT', '.FITS')):
					continue
				info = FileInfo(path)
				files.append(info)
			Session.add_file(self._session, *files)
			
		def process_removed(self, names : list[str]):
			files = []
			for name in names:
				if name not in self._session.included_files:
					continue
				file = self._session.included_files[name]
				files.append(file)
			Session.remove_file(self._session, *files)

	def add_file(self, *items: FileInfo):
		pass
	def remove_file(self, *items: FileInfo):
		pass
		
	def __init__(self, name: str, working_dir : str, auto_start : bool = True):
		super().__init__(name, working_dir)
		self._watcher = None
		if auto_start:
			self.begin_scan()
	
	def begin_scan(self):
		if self._watcher is None or self._watcher._stop is True:
			self._watcher = ScanSession.DirectoryWatcher(self)
		self._watcher.start()

	def end_scan(self):
		if self._watcher is not None:
			self._watcher.stop()

	def __item_added__(self, added : Sequence[FileInfo]): 
		print ("Added", added)
	def __item_removed__(self, removed : Sequence[FileInfo]): 
		print ("Removed", removed)
	
	def __export__(self) -> AttrDict:
		attr = super().__export__()
		attr['working_dir'] = self.working_dir.replace("\\", "/")
		return attr
	
	@classmethod
	def __import__(cls, attributes: AttrDict) -> Self:
		session= cls(attributes['name'], attributes['working_dir'], auto_start= False)
		session.archetype = attributes['archetype']
		session.included_files = attributes['included_files']
		session.included_stars = attributes['included_stars']
		return session