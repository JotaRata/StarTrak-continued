from .protocols import Parser, ParsedOutput, STException


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
		words = text_input.split(' ')

		for word in words:
			if any(word == kw for kw in _DISALLOWED_PY_KW):
				raise STException('Forbidden keywords at input')
		if not text_input:
			return ParsedOutput((None, 'none'))

		if '=' in text_input and not '==' in text_input:
			return ParsedOutput((text_input, 'exec'))
		else:
			return ParsedOutput((text_input, 'eval'))
		
class ShellParser(Parser):
	def parse(self, text_input: str) -> ParsedOutput:
		words = text_input.split(' ')

		for word in words:
			if any(word == kw for kw in _DISALLOWED_SH_KW):
				raise STException('Forbidden keywords at input')
		return ParsedOutput((text_input,))
	
class StartrakParser(Parser):
	def parse(self, text_input: str) -> ParsedOutput:
		return ParsedOutput((text_input,))
	