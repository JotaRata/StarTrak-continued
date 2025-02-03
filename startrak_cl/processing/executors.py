from io import StringIO
import subprocess
from typing import Any

from startrak_cl import STException, _globals
from startrak_cl.commands import Command, _AbstractCommandMeta, Optional, Parameter
from .protocols import ChainedOutput, Output, ParsedOutput
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
		console = _globals.CONSOLE_INSTANCE
		if type(parsed_data) is ParsedOutput:
			command, args, printable = parsed_data
			if not command: return

			command = get_command(command)
			parameters = self.parse_arguments(command, args)
			retval = command.execute(*parameters, printable= printable)

		elif type(parsed_data) is ChainedOutput:
			retval = None
			stdout = console.output.stdout
			for out in parsed_data.outputs:
				if type(out) is ParsedOutput:
					command, args, printable = out
				
				if not command: return
				if retval:
					new_args = [retval.strip()] + args
				else:
					new_args = args

				command = get_command(command)
				parameters = self.parse_arguments(command, new_args)

				if printable:
					command.execute(*parameters, printable= True)
					return
				try:
					output_buffer = StringIO()
					console.output.stdout = output_buffer
					command.execute(*parameters, printable= True)
					retval = output_buffer.getvalue()
				except:
					raise
				finally:
					output_buffer.close()
					console.output.stdout = stdout


	def parse_arguments(self, command : type[Command], args : list[str]):
		parameters = command.init_params()

		positional = [param for param in parameters if type(param) is Parameter]
		optional  = [param for param in parameters if type(param) is Optional]

		output_values = dict[str, Any]()

		if len(args) < len(positional):
			raise STException(f'Not enough parameters for command "{command.get_name()}"')


		def apply_attributes(parameter : Parameter, arg : str):
			value = arg
			if hasattr(parameter, 'map_function'):
				value = parameter.map_function(value)
			if hasattr(parameter, 'type_cast'):
				value = parameter.type_cast(value)
			if hasattr(parameter, 'validate_function'):
				if parameter.validate_function(value) == False:
					raise STException(f'Invalid parameter "{arg}" for command "{command.get_name()}"')
			return value
		
		for i, param in enumerate(sorted(optional, key= lambda x: x.is_implicit)):
			arg_index = -1
			for j, arg in enumerate(args):
				is_keyword = (arg.startswith('--') and param.name == arg[2:]) or (arg.startswith('-') and param.short_name == arg[1:])
				is_implicit = param.is_implicit and not arg.startswith('-')
				
				if is_keyword or is_implicit:
					arg_index = j
					break
			
			if arg_index >= 0:
				if param.type_cast is bool:
					output_values[param.name] = True
				elif is_implicit:
					value = apply_attributes(param, args[arg_index])
					output_values[param.name] = value
				else:
					if arg_index + 1 >= len(args):
						raise STException(f'Missing parameter value for parameter "{param.name}" in command "{command.get_name()}"')
					value = apply_attributes(param, args[arg_index + 1])
					output_values[param.name] = value
					args.pop(arg_index + 1)
				args.pop(arg_index)
			else:
				value = apply_attributes(param, param.default_value)
				output_values[param.name] = value
				
		for i, param in enumerate(positional):
			value = apply_attributes(param, args.pop(i))
			output_values[param.name] = value
			
		if len(args) != 0:
			raise STException(f'Unexpected parameters: {args} for command {command.get_name()}')
		return [output_values[param.name] for param in parameters]