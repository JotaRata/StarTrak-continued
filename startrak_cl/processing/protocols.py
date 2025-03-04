import re
from typing import NamedTuple, Protocol


class Output(Protocol):
	pass

class ParsedOutput(NamedTuple):
	command : str
	args : list[str]
	printable : bool = True
class PipedOutput(NamedTuple):
	outputs : list[ParsedOutput]
class RedirectedOutput(NamedTuple):
	output : Output
	varname : str

class Parser(Protocol):
	_REG_PATTERN = re.compile(r'\"([^\"]+)\"|(\S+)')
	def parse(self, text_input : str) -> ParsedOutput: ...
	def match(self, text : str):
		return [m[0] if m[0] else m[1] for m in Parser._REG_PATTERN.findall(text)]
	
class Executor(Protocol):
	def __init__(self, execution_context : dict[str, object], **kwargs) -> None: ...
	def execute(self, parsed_data : ParsedOutput) -> str: ...
