from ast import literal_eval
import os
import subprocess
from typing import Any

from startrak_cl.commands import Command, _AbstractCommandMeta, Optional, Parameter
from .protocols import ChainedOutput, Output, ParsedOutput, PipedOutput, STException
from .protocols import Executor

def get_commands():
	return _AbstractCommandMeta.registered_commands

def get_command(name : str) -> Command:
	if name not in get_commands():
		raise STException(f'Command not found: {name}')
	return get_commands()[name]


class PythonExecutor(Executor):
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

class ShellExecutor(Executor):
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
		
class StartrakExecutor(Executor):
	def __init__(self, execution_context: dict[str, object], **kwargs) -> None:
		self.execution_context = execution_context

	def execute(self, parsed_data: Output) -> str:
		if type(parsed_data) is ParsedOutput:
			command, args, printable = parsed_data
			if not command: return

			command = get_command(command)
			parameters = self.parse_arguments(command, args)
			retval = command.execute(*parameters, printable= printable)

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

				command = get_command(command)
				parameters = self.parse_arguments(command, new_args)
				retval = command.execute(*parameters, printable= printable)

	def parse_arguments(self, command : type[Command], args : list[str]):
		parameters = command.init_params()

		positional = [param for param in parameters if type(param) is Parameter]
		optional  = [param for param in parameters if type(param) is Optional]

		output_values = dict[str, Any]()

		assert len(args) >= len(positional), f'Not enough parameters for command "{command.get_name()}"'


		def apply_attributes(parameter : Parameter, arg : str):
			value = arg
			if hasattr(parameter, '_map'):
				value = parameter._map(value)
			if hasattr(parameter, '_type'):
				value = parameter._type(value)
			if hasattr(parameter, '_validator'):
				assert parameter._validator(value), f'Invalid parameter "{arg}" for command "{command.get_name()}"'
			return value
		
		for i, param in enumerate(sorted(optional, key= lambda x: x._imp)):
			arg_index = -1
			for j, arg in enumerate(args):
				is_keyword = (arg.startswith('--') and param._name == arg[2:]) or (arg.startswith('-') and param._short == arg[1:])
				
				if is_keyword or (param._imp and not arg.startswith('-')):
					arg_index = j
					break
			
			if arg_index >= 0:
				if param._type is bool:
					output_values[param._name] = True
				elif param._imp:
					value = apply_attributes(param, args[arg_index])
					output_values[param._name] = value
					args.pop(arg_index)
				else:
					assert arg_index + 1 < len(args), f'Missing parameter value for parameter "{param._name}" in command "{command.get_name()}"'
					value = apply_attributes(param, args[arg_index + 1])
					output_values[param._name] = value
					args.pop(arg_index + 1)
					args.pop(arg_index)
			else:
				value = apply_attributes(param, param._default)
				output_values[param._name] = value
				
		for i, param in enumerate(positional):
			value = apply_attributes(param, args[i])
			output_values[param._name] = value

		assert len(args) == 0, f'Unexpected parameters: {args} for command {command.get_name()}'
		return [output_values[param._name] for param in parameters]