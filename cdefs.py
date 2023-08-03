from io import TextIOWrapper
import os
from os.path import relpath, join, splitext, isfile

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
	out_path = join(dir, splitext(name)[0] + '.pxd')
	out = None	# Used to preview
	if isfile(out_path): 
		print('Skipping alreaady written file: ', out_path)
		continue
	with open(path, 'r') as file:
		with open(out_path, 'w') as out: # Comment this line to preview
			print('-'*50)
			print('Writing definition file to', out_path)
			write('# Auto generated Cython definitions', out)
			write(f'# file: "{path}"\n', out)
			prev = ''  # previous line
			is_class = False
			for line in file:
				_line = line.lstrip()

				# include imports
				if 'import' in _line:
					write(_line[:-1], out)

				# include functions
				if _line.startswith(('cdef', 'cpdef')):
					is_class = 'class' in line
					
					# include __init__ but  not private methods
					if '__' in _line and not '__init__' in _line: 
						continue

					if all([m in _line for m in ('(', ')', ':')]):
						write(line[:-1] + ' pass', out)

				prev = line