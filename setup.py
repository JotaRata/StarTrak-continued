import numpy
from setuptools import setup, Extension
# from Cython.Build import cythonize
from mypyc.build import mypycify
import os	
from os.path import relpath, splitext, join

def scan_files():
	cwd = os.getcwd()
	for path, _, files in os.walk(cwd + '/startrak/types'):
		for f in files:
			if not f.endswith('.py'): continue
			rel =  relpath(join(path, f), cwd)
			yield (splitext(rel)[0].replace(os.sep, '.'),  rel)

paths = [path for module, path in scan_files()]

setup(
		name= 'startrak',
		version="0.1",
		ext_modules=mypycify(paths),
		zip_safe=False,
		include_dirs=[numpy.get_include()]
)
