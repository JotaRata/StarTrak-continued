from startrak_cl import STException
from .protocols import PipedOutput, Parser, ParsedOutput, RedirectedOutput
from startrak_cl.processing.executors import get_command

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
			return ParsedOutput(None, ['none'])

		if '=' in text_input and not '==' in text_input:
			return ParsedOutput(text_input, ['exec'])
		else:
			return ParsedOutput(text_input, ['eval'])
		
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
		varname = None
		if '>>' in words:
			pipe_idx, varname = self.parse_redirect(words)
			words = words[:pipe_idx]

		if not '|' in words:
			return self.parse_single(words, var_name= varname)
		else:
			return self.parse_multiple(words, var_name= varname)

	def parse_single(self, words, chained= False, printable= True, var_name: str = None):
		cmd_name, *args = words
		if not args:
			args = []

		# Check for arguments
		chain_char = 1 if chained else 0
		command = get_command(cmd_name)
		if not command:
			raise STException(f'No command named "{cmd_name}"')
		

		output = ParsedOutput(cmd_name, args, printable)
		if var_name:
			output =  RedirectedOutput(output, var_name)
		return output
	
	def parse_multiple(self, words : list, var_name: str = None):
		count = words.count('|')
		outputs = []
		index = -1
		for i in range(count + 1):
			next_index = None
			if i != count:
				next_index = words.index('|', index + 1)
			sliced = words[index + 1: next_index]
			index = next_index
			parsed_output = self.parse_single(sliced, i > 0, i == count, var_name if i == count else None)
			outputs.append(parsed_output)
		return PipedOutput(outputs)

	def parse_redirect(self, words : list[str], ):
		if words.count('>>') > 1 or words[-2] != '>>':
			raise STException('Invalid syntax')
		index = words.index('>>')
		name = words[-1]
		return index, name


