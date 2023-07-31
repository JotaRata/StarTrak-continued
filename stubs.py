from io import TextIOWrapper
import os
from os.path import relpath, join, splitext

def scan_files():
	cwd = os.getcwd()
	for path, _, files in os.walk(cwd + '/startrak'):
		for f in files:
			if not f.endswith('.pyx'): continue
			yield join(path, f), f, path

def write(line :str,  file : TextIOWrapper = None):
	if not file: 
		print(line)
		return
	file.write(line + '\n')

for path, name, dir in scan_files():
	out_path = join(dir, splitext(name)[0] + '.pyi')
	out = None	# Used to preview

	with open(path, 'r') as file:
		with open(out_path, 'w') as out:
			print('Writing stub file to', out_path)
			write('# Auto generated stub')
			write(f'# file: "{path}"\n')
			for line in file:
				_line = line.lstrip()

				# include imports
				if 'import' in _line:
					write(_line[:-1], out)

				# include cython classes
				if _line.startswith(('cdef class', 'class')):
					write('\n' + line[:-1].replace('cdef ', ''), out)
				
				# include functions
				if _line.startswith(('def')):
					# include __init__ but  not private methods
					if ('__' in _line or '_' in _line[len('def '):]) and not '__init__' in _line: continue
					
					# replace pass with ellipsis
					if  not _line.rstrip().endswith('pass'):
						write(line[:-1] + ' ...', out)
					else:
						write(line[:-1].replace('pass', '...'), out)
				
				# include docstring, comments
				if _line.startswith(('#', '"""', "'''")):
					write(line[:-1], out)