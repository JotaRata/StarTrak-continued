from startrak.events import NamedEvent


def extension_method(target_cls, static = False, name = None):
		def decorator(func):
				if static:
					def wrapper(*args, **kwargs): return func( *args, **kwargs) # type: ignore
				else:
					def wrapper(self, *args, **kwargs): return func(*args, **kwargs)
				
				setattr(target_cls, func.__name__ if name is None else name, wrapper)
				return wrapper
		return decorator

def called_by(named_event : str):
	def decorator(func):
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		NamedEvent.register_to(named_event, wrapper)
		return wrapper
	return decorator