from typing import Final
APPNAME : Final[str] = "StarTrak"
VERSION : Final[str] = "1.0.0"

try:
	__compiled__ = False
	from .collections import position
	from .collections import native_array
	from . import numeric
	from . import classes
	from . import abstract
	from .collections import starlist
	from .collections import filelist
except:
	__compiled__ = True
	from startrak.native.collections import position
	from startrak.native.collections import native_array
	from startrak.native import numeric
	import startrak.native.classes as classes
	import startrak.native.abstract as abstract
	from startrak.native.collections import starlist
	from startrak.native.collections import filelist


Position = position.Position
PositionLike = position.PositionLike
PositionArray = position.PositionArray
Array = native_array.Array

Star = classes.Star
ReferenceStar = classes.ReferenceStar
FileInfo = classes.FileInfo
Header = classes.Header
HeaderArchetype = classes.HeaderArchetype
PhotometryResult = classes.PhotometryResult
TrackingSolution = classes.TrackingSolution

StarList = starlist.StarList
FileList = filelist.FileList

Session = abstract.Session
PhotometryBase = abstract.PhotometryBase
Tracker = abstract.Tracker
StarDetector = abstract.StarDetector


