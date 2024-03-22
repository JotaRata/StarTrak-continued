from ast import literal_eval
import os
import subprocess
from .protocols import ChainedOutput, Output, ParsedOutput, PipedOutput, STException
from .protocols import Executor
import base.commands
from base import get_command
import startrak

class PythonExcecutioner(Executor):
	def __init__(self, execution_context: dict[str, object], **kwagrs) -> None:
		self._globals = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command, mode, _ = parsed_data
		if mode != ['none']:
			command = command.replace(chr(0), '')
		if mode == ['eval']:
			result = eval(command, self._globals)
			if result is not None:
				print(repr(result))
		elif mode == ['exec']:
			exec(command, self._globals)

class ShellExecutioner(Executor):
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
			print(output)
		except Exception as e:
			raise STException(f"Error executing shell command: {e}")
		
class StartrakExecutioner(Executor):
	def __init__(self, execution_context: dict[str, object], **kwargs) -> None:
		self.execution_context = execution_context

	def execute(self, parsed_data: Output) -> str:
		varname = None
		if type(parsed_data) is PipedOutput:
			varname = parsed_data.varname
			parsed_data = parsed_data.output

		if type(parsed_data) is ParsedOutput:
			command, args, printable = parsed_data
			if not command: return

			call = get_command(command)
			retval = call(args, printable)

		elif type(parsed_data) is ChainedOutput:
			retval = None
			for out in parsed_data.outputs:
				if type(out) is ParsedOutput:
					command, args, printable = out
				elif type(out) is PipedOutput:
					command, args, printable = out.output
					varname = out.varname
				if not command: return
				if retval:
					new_args = args + [retval]
				else:
					new_args = args

				call = get_command(command)
				retval = call(new_args, printable)

		if varname:
			if not retval or not retval.obj:
				raise STException(f'Command "{command}" value cannot be exported to Python')
			self.execution_context[varname] = retval.obj