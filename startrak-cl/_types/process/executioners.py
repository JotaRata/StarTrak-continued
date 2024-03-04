from ast import literal_eval
import subprocess
from .protocols import ParsedOutput, STException
from .protocols import Executioner
from _types._lang import get_method

class PythonExcecutioner(Executioner):
	def __init__(self, execution_context: dict[str, object], **kwagrs) -> None:
		self._globals = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command, (mode, ) = parsed_data
		if mode != 'none':
			command = command.replace(chr(0), '')
		if mode == 'eval':
			result = eval(command, self._globals)
			if result:
				return repr(result)
		elif mode == 'exec':
			exec(command, self._globals)
		return ''

class ShellExecutioner(Executioner):
	def __init__(self, execution_context: dict[str, object], **kwargs) -> None:
		self.execution_context = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command = parsed_data.command
		if not command:
			return ""
		command = command.replace(chr(0), '')
		try:
			result = subprocess.run(command, shell=True, capture_output=True, text=True)
			output = result.stdout.strip() if result.stdout else ""
			if result.returncode != 0:
					raise STException(f"Shell command failed: {result.stderr.strip()}")
			return output
		except Exception as e:
			raise STException(f"Error executing shell command: {e}")
		
class StartrakExecutioner(Executioner):
	def __init__(self, execution_context: dict[str, object], **kwargs) -> None:
		self.execution_context = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command, args = parsed_data
		if not command:
			return ""
		
		func, targs, ret = get_method(command)
		if len(args) != len(targs):
			raise STException(f'"{command}" requires {len(targs)} arguments, given {len(args)}')
		
		values = []
		for i, (tneed, given) in enumerate(zip(targs, args)):
			try:
				value = literal_eval(given)
			except:
				value = repr(given)

			if type(value).__name__ != tneed:
				raise STException(f'"{command}" argument #{i} needs to be of type "{tneed}", "{type(value).__name__}" given')
			values.append(value)
		
		source = func(*values)
		print(source)
		output = str(eval(source, self.execution_context))

		return output