from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("startrak.io", ["startrak/io.pyx"]),
    Extension("startrak.types", ["startrak/types.pyx"])
]

setup(
    name= 'startrak',
    version="0.1",
    ext_modules=cythonize(extensions),
    zip_safe=False,
)