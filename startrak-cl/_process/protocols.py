import re
from typing import Literal, NamedTuple, Protocol

class ParsedOutput(NamedTuple):
	command : str
	args : tuple[str,...]


class Parser(Protocol):
	_REG_PATTERN = re.compile(r'\"([^\"]+)\"|(\S+)')
	def parse(self, text_input : str) -> ParsedOutput: ...
	def match(self, text : str):
		return [m[0] if m[0] else m[1] for m in Parser._REG_PATTERN.findall(text)]
class Executor(Protocol):
	def __init__(self, execution_context : dict[str, object], **kwagrs) -> None: ...
	def execute(self, parsed_data : ParsedOutput) -> str: ...
class STException(Exception):
	pass
