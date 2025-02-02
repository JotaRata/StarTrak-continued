
import os
from startrak_cl.commands import Command, Parameter
from startrak_cl.processing.protocols import STException
from startrak_cl.utils.casters import path


class ChangeDirectoryCommand(Command,
							alias='cd',
							description='Changes the current working directory to the specified path.',
							author='JotaRata - Adapted from GNU'):
	def init_params():
		return [
			Parameter('path')
				.with_description('The path of the directory to change to. This should be a valid directory path on your filesystem.')
				.with_type(path)
				.with_validation(lambda l: len(l) == 1)
		]
	
	def execute(paths : list[str], *args, **kwargs):
		path = paths[0]
		if not os.path.isdir(path):
			raise STException('Path is not a directory.')
		os.chdir(path)


class CurrentDirectoryCommand(Command,
										alias= 'pwd',
										description= 'Prints the current working directory',
										author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return []
	
	def execute(*args, **kwargs):
		cwd = os.getcwd()

		if os.name == 'nt':
			cwd = cwd.replace('\\', '/')
		print(cwd)

class QuitCommand(Command,
						alias= 'quit',
						description= 'Immediatly quits the program.',
						author= 'JotaRata - Adapted from GNU'):
		def init_params():
			return []
		
		def execute(*args, **kwargs):
			quit()