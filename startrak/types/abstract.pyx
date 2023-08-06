__methods__ = dict[str, list]()

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
		if not cls.__base__.__name__ in __methods__:
			cls.__base__.__cls_init__()
		
		if (_base := cls.__base__) is not Interface and _base.__name__ in __methods__:
			__methods__[cls.__name__] = __methods__[_base.__name__] 
		else:
			__methods__[cls.__name__] = []
		for name, value in cls.__dict__.items():
			if callable(value) and getattr(value, '__isabstractmethod__', False):
				__methods__[cls.__name__].append(name)
		
		if cls.__base__ is not Interface:
			for method in __methods__[_base.__name__]:
				if method in cls.__dict__:
					__methods__[cls.__name__].remove(method)
	
	@classmethod
	def __initsubclass__(cls, subclass):
		for method in __methods__[cls.__name__]:
			if not callable(subclass.__dict__.get(method, None)):
				raise TypeError(f'{subclass.__name__} does not implement abstract method: {method}')

def abstract(func):
	def wrapper(*args, **kwargs):
		raise NotImplementedError(func.__name__)
		# return func(*args, **kwargs)
	setattr(wrapper, "__isabstractmethod__", True)
	return wrapper
