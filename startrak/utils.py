def extension_method(target_cls, static = False):
		def decorator(func):
				if static:
					def wrapper(*args, **kwargs): return func( *args, **kwargs)
				else:
					def wrapper(self, *args, **kwargs): return func(*args, **kwargs)
				
				setattr(target_cls, func.__name__, wrapper)
				return wrapper
		return decorator
