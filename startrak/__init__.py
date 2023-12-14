# type: ignore
from .native import Star, Position, PositionArray, StarList
from .native.ext import pprint
from .starutils import detect_stars, visualize_stars
from .sessionutils import *
from .native.utils import geomutils
from .io import *

APPNAME = "StarTrak"
VERSION = "1.0.0"
