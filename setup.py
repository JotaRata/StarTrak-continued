import os
import sys
from setuptools import setup
from Cython.Build import cythonize

os.chdir("./startrak")
setup(
    name= 'startrak',
    ext_modules=cythonize([
        "io.pyx",
        "types.pyx",
        # Add Cython-optimized files for submodules if needed
    ]),
)