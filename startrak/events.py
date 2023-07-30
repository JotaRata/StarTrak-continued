from typing import Callable


class Event():
	def __init__(self, *method_list):
		self._methods : list = method_list
	def add(self, function : Callable):
		if callable(function): self._methods.append(function)
	def remove(self, function : callable):
		if function in self._methods: self._methods.remove(function)
	def __call__(self, *args, **kwagrs):
		for function in self._methods: function(*args, **kwagrs)
	
class NamedEvent(Event):
	_named_events = dict[str, Event]()

	def __init__(self, name : str, *method_list):
		if not name: raise NameError('Name cannot be empty')
		super().__init__(*method_list)
		self.name = str(name)
		NamedEvent._named_events[self.name] = self
	
	def forget(self):
		NamedEvent._named_events.pop(self.name)
	def __repr__(self) -> str:
		return self.name +' : '+super().__repr__()
	
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
	def call_event(name : str, *args, **kwargs):
		if name in NamedEvent._named_events.keys():
			NamedEvent._named_events[name].__call__(*args, **kwargs)
	@staticmethod
	def register_to(named_event : str, function : Callable):
		if named_event in NamedEvent._named_events.keys():
			NamedEvent._named_events[named_event].add(function)
		else:
			NamedEvent(named_event, function)
	
def get_event(name : str):
	return NamedEvent.get_event(name)

def call_event(name : str):
	NamedEvent.call_event(name)

def register_to(named_event : str, function : Callable):
	NamedEvent.register_to(named_event, function)