from setuptools import setup, Extension
from Cython.Build import cythonize
import os	
from os.path import relpath, splitext, join

def scan_files():
	cwd = os.getcwd()
	for path, _, files in os.walk(cwd + '/startrak'):
		for f in files:
			if not f.endswith('.pyx'): continue
			rel =  relpath(join(path, f), cwd)
			yield (splitext(rel)[0].replace(os.sep, '.'),  [rel])

extensions = [Extension(*sources) for sources in scan_files()]

setup(
		name= 'startrak',
		version="0.1",
		ext_modules=cythonize(extensions),
		zip_safe=False,
)
