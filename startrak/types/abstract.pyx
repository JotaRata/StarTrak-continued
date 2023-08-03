cdef class Interface:
	def __cinit__(self):
		cls = type(self)
		if cls is Interface or cls.__base__ is Interface:
			raise TypeError(f'{cls.__name__} is marked as an Interface and cannot be instantiated')
		assert isinstance(self, Interface)
		cls.__cls_init__()
		cls.__base__.__initsubclass__(cls)
	
	@classmethod
	def __cls_init__(cls):
		if cls is Interface: return
		if not getattr(cls.__base__, "__initialized__", False):
			cls.__base__.__cls_init__()
		methods = set(getattr(cls, "__methods__", set()))
		for name, value in cls.__dict__.items():
			if callable(value) and getattr(value, "__isabstractmethod__", False):
				methods.add(name)
			if (_base := cls.__base__) is not Interface:
				if callable(value) and name in _base.__methods__:
					methods.remove(name)

		cls.__methods__ = frozenset(methods)
		cls.__initialized__ = True
	
	@classmethod
	def __initsubclass__(cls, subclass):
		for method in cls.__methods__:
				if not callable(subclass.__dict__.get(method, None)):
						raise TypeError(f'{subclass.__name__} does not implement abstract method: {method}')

def abstract(func):
	def wrapper(*args, **kwargs):
		return func(*args, **kwargs)
	setattr(wrapper, '__isabstractmethod__', True)
	return wrapper
