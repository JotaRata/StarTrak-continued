from ast import literal_eval
import os
import subprocess
from .protocols import ParsedOutput, STException
from .protocols import Executor
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
			if result:
				return repr(result)
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
			return output
		except Exception as e:
			raise STException(f"Error executing shell command: {e}")
		
class StartrakExecutioner(Executor):
	def __init__(self, execution_context: dict[str, object], **kwargs) -> None:
		self.execution_context = execution_context

	def execute(self, parsed_data: ParsedOutput) -> str:
		command, args = parsed_data
		if not command:
			return ""
		self.match(command, args)
		# todo: add somehow in parser
		# if len(args) > 0:
		# 	raise STException(f'Unexpected keywords "{args}" in "{command}"')
		return ''
	
	def match(self, command, args):
		def get_kw(arg, *types):
			if len(args) < 1 + len(types): 
				return False
			if arg not in args: 
				return False
			if len(types) == 0:
				return True
			idx = args.index(arg)
			values = []
			for j, _type in enumerate(types, 1):
				next_ = args[idx + j]
				try:
					value = _type(next_)
				except:
					raise STException(f'Invalid argument type for "{command}" at position #{j}')
				values.append(value)
			args.pop(idx)
			for i in range(len(values)):
				args.pop(idx)

			if len(values) > 1:
				return values
			return value
		
		def get_arg(pos, _type):
			if pos > len(args):
				raise STException(f'Expected argument at position #{pos + 1} of the function "{command}"')
			try:
				value = _type(args[pos])
			except:
				raise STException(f'Invalid argument type for "{command}" at position #{pos + 1}')
			args.pop(pos)
			return value
		
		match command:
			case 'session':
				fold = get_kw('-f', int)
				new = get_kw('-new', str, str)
				if '-new' in args and not new:
					raise STException('Keyword "-new" expected two arguments: name and sessionType')
				if new:
					out = get_kw('--v')
					s = startrak.new_session(new[0], new[1])
					if out:
						startrak.pprint(s,  fold if fold else 1)
					return
				startrak.pprint(startrak.get_session(), fold if fold else 1)

			case 'cd':
				path = get_arg(0, str)
				os.chdir(path)
			case 'ls':
				if len(args) == 0:
					path = os.getcwd()
				else:
					path = get_arg(0, str)
				print(path)
				for path in os.scandir(path):
					print(' ',os.path.basename(path) + ('/' if os.path.isdir(path) else ''))

			case 'open':
				path = get_arg(0, str)
				out = get_kw('--v')
				s = startrak.load_session(path)
				if out:
					fold = get_kw('-f', int)
					startrak.pprint(s,  fold if fold else 1)
			
			case 'add':
				mode = get_arg(0, str)
				out = get_kw('--v')
				if not startrak.get_session():
					raise STException('No session to add to, create one using session -new')
				match mode:
					case 'file':
						path = get_arg(1, str)
						file = startrak.load_file(path, append= True)
						if out:
							fold = get_kw('-f', int)
							startrak.pprint(file, fold if fold else 1)
					case _:
						raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')