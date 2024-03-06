from .protocols import Parser, ParsedOutput, STException
from _wrapper.base import get_command

_DISALLOWED_PY_KW = ('import', 'os', 'sys', 'raise', 
							'input', 'class', 'open', 'with', 
							'assert', 'exec', 'eval', 'compile',
							'subprocess')
_DISALLOWED_SH_KW = ('sudo', 'bash', 'sh', 'cmd', 
							'powershell', 'pwsh', 'exec', 
							'start', 'python', 'shutdown', 
							'reboot', 'init')

class PythonParser(Parser):
	def parse(self, text_input : str) -> ParsedOutput:
		words = self.match(text_input.strip())

		for word in words:
			if any(word == kw for kw in _DISALLOWED_PY_KW):
				raise STException('Forbidden keywords at input')
		if not text_input:
			return ParsedOutput(None, ('none', ))

		if '=' in text_input and not '==' in text_input:
			return ParsedOutput(text_input, ('exec', ))
		else:
			return ParsedOutput(text_input, ('eval', ))
		
class ShellParser(Parser):
	def parse(self, text_input: str) -> ParsedOutput:
		words = self.match(text_input.strip())

		for word in words:
			if any(word == kw for kw in _DISALLOWED_SH_KW):
				raise STException('Forbidden keywords at input')
		return ParsedOutput(text_input, ( ))
	
class StartrakParser(Parser):
	def parse(self, text_input: str) -> ParsedOutput:
		if not text_input:
			return ParsedOutput(None, ('none',))
		words = self.match(text_input.strip())
		cmd_name, *args = words
		if not args:
			args = []

		# Check for arguments
		command = get_command(cmd_name)
		if not command:
			raise STException(f'No command named "{cmd_name}"')
		if len(args) < command.count_positional:
			raise STException(f'Not enough arguments for "{cmd_name}"')
		if len(args) > (command.count_positional + command.count_optional + command.count_kws):
			raise STException(f'Too many arguments for "{cmd_name}"')
		
		for a in args:
			if a.startswith('-') and a not in command.keywords:
				raise STException(f'Unknown keyword "{a}" in command "{cmd_name}"')
			
		return ParsedOutput(cmd_name, args)
