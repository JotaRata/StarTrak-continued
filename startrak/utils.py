def extension_method(target_cls, static = False, name = None):
		def decorator(func):
				if static:
					def wrapper(*args, **kwargs): return func( *args, **kwargs) # type: ignore
				else:
					def wrapper(self, *args, **kwargs): return func(*args, **kwargs)
				
				setattr(target_cls, func.__name__ if name is None else name, wrapper)
				return wrapper
		return decorator
