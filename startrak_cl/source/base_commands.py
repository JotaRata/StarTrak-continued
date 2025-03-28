
import os
import sys
from startrak_cl import STException
from startrak_cl.commands import Command, Optional, Parameter, get_active_console
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
	
	def execute(path : list[str], **kwargs):
		path = path[0]
		if not os.path.isdir(path):
			raise STException('Path is not a directory.')
		os.chdir(path)


class CurrentDirectoryCommand(Command,
							alias= 'pwd',
							description= 'Prints the current working directory',
							author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return []
	
	def execute(**kwargs):
		cwd = os.getcwd()

		if os.name == 'nt':
			cwd = cwd.replace('\\', '/')
		print(cwd)


class EchoCommand(Command,
					alias= 'echo',
					description= 'Prints the input to the screen.',
					author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return [
			Parameter('text')
				.with_description('The text to print to the screen.')
				.with_type(str)
		]
	
	def execute(text : str, **kwargs):
		console = get_active_console()
		text = console.remove_format(text)
		print(text)

class ClearCommand(Command,
						alias= 'clear',
						description= 'Clears the screen.',
						author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return []

	def execute(**kwargs):
		console = get_active_console()
		console.clear()

class QuitCommand(Command,
						alias= 'quit',
						description= 'Immediatly quits the program.',
						author= 'JotaRata - Adapted from GNU'):
		def init_params():
			return []
		
		def execute(*args, **kwargs):
			quit()

class CopyCommand(Command,
					alias= 'cp',
					description= 'Copies a file to another location.',
					author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return [
			Parameter('source')
				.with_description('The source file to copy.')
				.with_type(str),
			
			Parameter('destination')
				.with_description('The destination file to copy to.')
				.with_type(str)
		]
	
	def execute(source : str, destination : str, **kwargs):
		if not os.path.isfile(source):
			raise STException('Source is not a file.')
		
		if os.path.isdir(destination):
			destination = os.path.join(destination, os.path.basename(source))
		if os.path.exists(destination):
			raise STException('Destination already exists.')
		
		with open(source, 'rb') as src:
			with open(destination, 'wb') as dest:
				dest.write(src.read())

class MoveCommand(Command, 
					alias= 'mv',
					description= 'Moves a file to another location.',
					author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return [
			Parameter('source')
				.with_description('The source file to move.')
				.with_type(str),
			
			Parameter('destination')
				.with_description('The destination file to move to.')
				.with_type(str)
		]
	
	def execute(source : str, destination : str, **kwargs):
		if not os.path.isfile(source):
			raise STException('Source is not a file.')
		
		if os.path.isdir(destination):
			destination = os.path.join(destination, os.path.basename(source))
		if os.path.exists(destination):
			raise STException('Destination already exists.')
		
		os.rename(source, destination)

class RemoveCommand(Command,
					alias= 'rm',
					description= 'Removes a file or an empty directory.',
					author= 'JotaRata - Adapted from GNU'):
	def init_params():
		return [
			Parameter('target')
				.with_description('The file or directory to remove.')
				.with_type(str),
			Optional('recursive', 'r')
				.with_description('Recursively remove directories and their contents.')
				.with_type(bool),
		]
	
	def execute(target : str, recursive : bool = False, **kwargs):
		if not os.path.exists(target):
			raise STException('Target does not exist.')
		
		if os.path.isdir(target):
			if recursive:
				os.rmdir(target)
			else:
				raise STException('Target is a directory. Use -r to remove it recursively.')
		else:
			os.remove(target)
	