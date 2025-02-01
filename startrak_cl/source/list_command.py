import os

from startrak_cl.commands import Command, Optional, Parameter


class ListCommand(Command,
						alias = 'ls',
						description= 'List files in a directory',
						author= 'JotaRata'):
	
	def init_params():
		return [
			Optional('path', implicit= True)
				.with_description('The path to the directory for which files will be listed')
				.with_type(str)
				.with_default('.'),
			
			Optional('bok', 'b')
				.with_type(int)
				.with_default(0)
			]
	
	def execute(path : str, bok, *args, **kwargs):
		print(path)
		if bok:
			print('BOKKED', bok)
			return
		files = os.listdir(path)
		for file in files:
			print(file)