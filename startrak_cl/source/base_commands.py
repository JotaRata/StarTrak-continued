import math
import os
import stat
import time
from startrak_cl.commands import Command, Optional, Parameter, get_active_console
from startrak_cl.processing.protocols import STException
from startrak_cl.utils.casters import path

class ListCommand(Command,
						alias = 'ls',
						description= 'List files in a directory',
						author= 'JotaRata'):
	
	def init_params():
		return [
			Optional('path', implicit= True)
				.with_description('The path to the directory for which files will be listed')
				.with_type(path)
				.with_default([]),
			
			Optional('list', 'l'),
			Optional('columns', 'c')
				.with_type(int)
				.with_default(0)
			]
	
	def execute(path, list_mode, cols, printable= True, **kwargs):
		cwd = os.getcwd()
		paths = dict[str, list]()
		console = get_active_console()

		match path:
			case []:
				paths[cwd] = [(e.name, e.is_dir()) for e in os.scandir(cwd)]
			case [path]:
				if not os.path.exists(path):
					raise STException('Path not found')
				paths[path] = [(e.name, e.is_dir()) for e in os.scandir(path)]
			case _:
				for entry in path:
					dir_name = os.path.dirname(entry)
					if len(dir_name) == 0:
						dir_name = '.'
					rel = os.path.relpath(entry, dir_name)
					is_dir = os.path.isdir(entry)
					if dir_name not in paths:
						paths[dir_name] = [(rel, is_dir)]
					else:
						paths[dir_name].append((rel, is_dir))

		if printable:
			buffer = console.buffer()

			max_length = max([len(file) for dir in paths for (file, _) in paths[dir]])
			for dir in paths:
				if os.name == 'nt':
					dir = dir.replace(r'\\', '/')	
				if len(paths) > 1:
					buffer.write(f'{dir}: \n')

				if not list_mode:
					if cols == 0:
						cols = min(max(1, console.width // max_length), 4)
						col_width = console.width // cols
					else:
						col_width = console.width // cols
						max_length = min(max_length, col_width - 3)
						
					ListCommand.list_columns(buffer, paths[dir], cols)
				else:
					ListCommand.list_stats(buffer, paths[dir], dir)
			console.write(buffer.getvalue())

	def list_columns(buffer, paths, columns):
		console = get_active_console()

		rows = math.ceil(len(paths) / columns)
		col_width = console.width // columns

		for row in range(rows):
			for column in range(columns):
				index = row + column * rows
				if index >= len(paths):
					break
				
				file, is_dir = paths[index]
				if len(file) > col_width:
					file = file[:col_width] + '..'
				if ' ' in file:
					file = f"'{file}'"

				file = file.ljust(col_width)
				buffer.write(console.format( file, 'blue' if is_dir else 'green'))
			buffer.write('\n')
		buffer.write('\n')

	def list_stats(buffer, paths, directory):
		console = get_active_console()
		
		buffer.write(f'Total: {len(paths)}\n')
		columns = list[str]()
		for file, is_dir in paths:
			stats = os.stat(f'{directory}/{file}')
			if ' ' in file:
				file = f"'{file}'"
			
			columns.append( stat.filemode(stats.st_mode) )
			columns.append( str(stats.st_uid) )
			columns.append( str(stats.st_gid) )
			columns.append( str(stats.st_size) )
			columns.append( time.ctime(stats.st_mtime) )
			buffer.write(' '.join( (str.rjust(col, 8) for col in columns) ) + ' ')
			buffer.write(console.format(file, 'blue' if is_dir else 'green'))
			
			buffer.write('\n')
			columns.clear()
		buffer.write('\n')

	