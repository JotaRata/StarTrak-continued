import subprocess
from . import ParsedOutput, STException
from process import Executioner

class PythonExcecutioner(Executioner):
	def __init__(self, execution_context: dict[str, object], **kwagrs) -> None:
		self._globals = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		prefix = '> '
		command, mode = parsed_data.data
		if mode != 'none':
			command = command.replace(chr(0), '')
		if mode == 'eval':
			result = eval(command, self._globals)
			if result:
				return prefix + repr(result)
		elif mode == 'exec':
			exec(command, self._globals)
		return prefix

class ShellExecutioner(Executioner):
	def __init__(self, execution_context: dict[str, object], **kwargs) -> None:
		self.execution_context = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command = parsed_data.data[0]
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
		return parsed_data.data[0]