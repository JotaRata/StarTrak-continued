from io import TextIOWrapper
import os
from os.path import relpath, join, splitext
from re import split

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
		with open(out_path, 'w') as out: # Comment this line to preview
			print('Writing stub file to', out_path)
			write('# Auto generated stub', out)
			write(f'# file: "{path}"\n', out)
			prev = ''  # previous line
			for line in file:
				_line = line.lstrip()

				# include imports
				if 'import' in _line:
					write(_line[:-1], out)

				# include cython classes
				if _line.startswith(('cdef class', 'class')):
					write('\n' + line[:-1].replace('cdef ', ''), out)
				
				# include static typed variables
				if _line.startswith('cdef') and not 'class' in _line:
					if (not 'public' in _line) and (not 'readonly' in _line): continue
					split_line = _line.rstrip().split(' ')
					if split_line[0] != 'cdef': continue # somehow line doesnt start with cdef
					
					indent = line[: line.index('cdef')] # yes I know there are better ways
					if len(split_line) == 4: # cdef public type var
						_type = split_line[2]
						_var = split_line[3]
						write(indent + _var + ' : ' + _type, out)
					
					if len(split_line) == 3: # cdef public var
						_var = split_line[2]
						write(indent + _var, out)

					# Non public fields are ignored
				
				# include instance variables through a special notation
				# #@self.variable
				_sprefix = '#@self.'
				if _line.startswith(_sprefix):
					indent = line[: line.index(_sprefix) ]
					write(indent + _line[_line.index(_sprefix) + len(_sprefix): -1], out)

				# include functions
				if _line.startswith(('def', 'cpdef')):
					# include __init__ but  not private methods
					if ('__' in _line or '_' in _line[len('def '):]) and not '__init__' in _line: continue
					
					# replace pass with ellipsis
					if  not _line.rstrip().endswith('pass'):
						write(line[:-1].replace('cpdef', 'def') + ' ...', out)
					else:
						write(line[:-1].replace('cpdef', 'def').replace('pass', '...'), out)

				if 'pass' in _line and 'class' in prev:
					write(_line[:-1].replace('pass', '...'), out)
				
				# include docstring, comments
				if _line.startswith(('#', '"""', "'''")) and not _sprefix in _line:
					write(line[:-1], out)
				
				prev = line