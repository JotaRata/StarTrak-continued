from re import A
from startrak.internals.types import InstantiationError


cdef class Interface:
	cdef set __methods__
	cdef bint __initialized__
	def __cinit__(self):
		cls = type(self)
		if cls is Interface or cls.__base__ is Interface:
			raise TypeError(f'{cls.__name__} is marked as an Interface and cannot be instantiated')
		assert isinstance(self, Interface)
		cls.__base__.__initsubclass__()
		cls.__base__.__subclasshook__(cls)

	@classmethod
	def __initsubclass__(cls, **kwargs):
		if getattr(cls, "__initialized__", False):
			return NotImplemented
		methods = getattr(cls, "__methods__", set())
		for name, value in cls.__dict__.items():
			if callable(value) and getattr(value, "__isabstractmethod__", False):
					methods.add(name)
		cls.__methods__ = frozenset(methods)
		cls.__initialized__ = True
	@classmethod
	def __subclasshook__(cls, subclass):
		if cls.__base__ is not Interface:
				return NotImplemented
		for method in cls.__methods__:
				if not callable(subclass.__dict__.get(method, None)):
						raise TypeError(f'{subclass.__name__} does not implement abstract method: {method}')

def abstract(func):
	def wrapper(*args, **kwargs):
		return func(*args, **kwargs)
	setattr(wrapper, '__isabstractmethod__', True)
	return wrapper

class Test(Interface):
	@abstract
	def foo(self, x): pass