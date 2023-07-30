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
		super().__init__(*method_list)
		self.name = str(name)
		NamedEvent._named_events[self.name, self]
	
	def forget(self):
		NamedEvent._named_events.pop(self.name)
	def __repr__(self) -> str:
		return self.name +' : '+super().__repr__()
	
	@staticmethod
	def get_events():
		return NamedEvent._named_events.values()
	def get_event(name : str):
		return NamedEvent._named_events[name]
	@staticmethod
	def register_to(named_event : str, function : Callable):
		if named_event in NamedEvent._named_events.keys():
			NamedEvent._named_events[named_event].add(function)
	