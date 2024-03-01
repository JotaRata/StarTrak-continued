from typing import NamedTuple, Protocol

class ParsedOutput(NamedTuple):
	data : tuple[str,...]

class Parser(Protocol):
	def parse(self, text_input : str) -> ParsedOutput: ...
class Executioner(Protocol):
	def __init__(self, execution_context : dict[str, object], **kwagrs) -> None: ...
	def execute(self, parsed_data : ParsedOutput) -> str: ...
class STException(Exception):
	pass

from . import parsers as parser
from . import executioners as execs