from setuptools import setup, Extension
from Cython.Build import cythonize
import os
from os.path import relpath, splitext

cwd = os.getcwd() + '/startrak'
extensions = [Extension("startrak." + splitext(path)[0], ['startrak/' + path ]) 
              for path in os.listdir(cwd) if path.endswith('.pyx')]

setup(
    name= 'startrak',
    version="0.1",
    ext_modules=cythonize(extensions),
    zip_safe=False,
)
