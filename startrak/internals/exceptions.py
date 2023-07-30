from typing import Any


class ImmutableError(Exception):
		def __init__(self, obj: Any):
			self._type = type(obj)
		def __str__(self) -> str:
			return f'Cannot assign attributes to {self._type} because is marked as immutable.'		

class InstantiationError(Exception):
		def __init__(self, obj : Any, alt : str =  None):
			self._type = type(obj)
			self._alt = alt
		def __str__(self) -> str:
			msg = f'Cannot create an instance of {self._type} directly'
			if self._alt: msg += f'\nTry using {self._alt}'
			return msg