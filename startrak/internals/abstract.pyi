# Auto generated stub
# file: "C:\Users\jjbar\Documents\GitHub\StarTrak-continued/startrak\internals\abstract.pyx"
from startrak.exceptions import *
from startrak.internals.types import FileInfo, HeaderArchetype, Header

class Interface: pass
def abstract(func): ...
# -------------- Classes -------------------

class Session(Interface):
		name : str
		working_dir : str
		archetype : HeaderArchetype
		included_files : set[FileInfo]
				# self.creation_time = datetime.now()
		def add_item(self, item : FileInfo | list[FileInfo]):  ...
		def remove_item(self, item : FileInfo | list[FileInfo]):  ...
		def set_archetype(self, Header header): ...
		def save(self, out): ...
