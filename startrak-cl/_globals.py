import os
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from console.consoleapp import ConsoleApp
	CONSOLE_INSTANCE : ConsoleApp

BASE_DIR = os.path.dirname(__file__)
assert len(BASE_DIR) > 0

CONSOLE_INSTANCE = None