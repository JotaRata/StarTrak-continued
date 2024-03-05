from typing import Literal, NamedTuple, Protocol

class ParsedOutput(NamedTuple):
	command : str
	args : tuple[str,...]


class Parser(Protocol):
	def parse(self, text_input : str) -> ParsedOutput: ...
class Executor(Protocol):
	def __init__(self, execution_context : dict[str, object], **kwagrs) -> None: ...
	def execute(self, parsed_data : ParsedOutput) -> str: ...
class STException(Exception):
	pass
