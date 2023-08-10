from typing import Any, Callable, ClassVar, Dict, List, Self


_TFunc = Callable[[Any], Any]
class Event():
	'''
		### Event handler
		Event handler class to delegate calls to other functions, use the event.add() method to subsribe a function to this event

		Example:
		```
			def f(x): print(x)
			def g(x): print(x + 1)
			event = Event(f, g) # or use event.add
			event(1) # prints: 1  2
		```
	'''
	def __init__(self, *method_list : _TFunc):
		self._methods : List[_TFunc] = list(method_list)
	def add(self, function : _TFunc):
		if callable(function): self._methods.append(function)
	def remove(self, function : _TFunc):
		if function in self._methods: self._methods.remove(function)
	def __call__(self, *args : Any, **kwagrs : Any):
		for function in self._methods: function(*args, **kwagrs)
	def __len__(self):
		return self._methods.__len__()
	def __repr__(self) -> str:
		return f'{type(self).__name__} object with {self.__len__()} bound methods.'
	
class NamedEvent(Event):
	'''
		Use this class to create globally accessed singleton events using a name

		Creating a NamedEvent will automatically register the event, you can use the default constuctor NamedEvent(name, *functions) but it's recommended to use the decorator '@called_by' from startrak.utils.

		You can call a named event by using the method call_event(name), an event can be unregistered using the forget() method.

		Example 1:
		```
			def f(x): print(x)
			event = NamedEvent('my_event', f)
			NamedEvent.call_event('my_event', 2) # you can also use event(2)
		```
		Example 2 (shortcut):
		```
			from startrak.utils import called_by
			from startrak.events import call_event
			# event will be created if it doesn't exist
			@called_by('my_event')
			def f(x): print(x)
			call_event('my_event', 2) # prints: 2
		```
	'''
	_named_events : ClassVar[Dict[str, Self]]

	def __init__(self, name : str, *method_list : _TFunc):
		if not name: raise NameError('Name cannot be empty')
		super().__init__(*method_list)
		self.name = str(name)
		NamedEvent._named_events[self.name] = self
	
	def forget(self):
		NamedEvent._named_events.pop(self.name)
	def __repr__(self) -> str:
		return f'{super().__repr__()} ({self.name = })'
	
	@staticmethod
	def get_events():
		return list(NamedEvent._named_events.values())
	@staticmethod
	def get_event(name : str):
		return NamedEvent._named_events[name]
	@staticmethod
	def forget_event(name : str):
		if name in NamedEvent._named_events.keys():
			NamedEvent._named_events[name].forget()
	@staticmethod
	def call_event(name : str, *args : Any, **kwargs : Any):
		if name in NamedEvent._named_events.keys():
			NamedEvent._named_events[name].__call__(*args, **kwargs)
	@staticmethod
	def register_to(named_event : str, function : _TFunc):
		if named_event in NamedEvent._named_events.keys():
			NamedEvent._named_events[named_event].add(function)
		else:
			NamedEvent(named_event, function)

def get_named_events():
		return list(NamedEvent._named_events.values()) 	# type: ignore
def get_event(name : str):
	return NamedEvent.get_event(name)

def call_event(name : str, *args : Any, **kwargs : Any):
	NamedEvent.call_event(name, *args, **kwargs)

def register_to(named_event : str, function : _TFunc):
	NamedEvent.register_to(named_event, function)

def called_by(named_event : str):
	def decorator(func : Callable[[Any], Any]):
		def wrapper(*args : Any, **kwargs : Any):
			return func(*args, **kwargs)
		NamedEvent.register_to(named_event, wrapper)
		return wrapper
	return decorator