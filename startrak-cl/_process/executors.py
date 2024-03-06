from ast import literal_eval
import os
import subprocess
from .protocols import ParsedOutput, STException
from .protocols import Executor
import _wrapper.funcs
from _wrapper.base import get_command
import startrak

class PythonExcecutioner(Executor):
	def __init__(self, execution_context: dict[str, object], **kwagrs) -> None:
		self._globals = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command, (mode, ) = parsed_data
		if mode != 'none':
			command = command.replace(chr(0), '')
		if mode == 'eval':
			result = eval(command, self._globals)
			print(repr(result))
		elif mode == 'exec':
			exec(command, self._globals)
		return ''

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

	def execute(self, parsed_data: ParsedOutput) -> str:
		command, args = parsed_data
		if not command:
			return ""
		
		call = get_command(command)
		if call:
			call(args)
		# todo: add somehow in parser
		# if len(args) > 0:
		# 	raise STException(f'Unexpected keywords "{args}" in "{command}"')
		return ''
	