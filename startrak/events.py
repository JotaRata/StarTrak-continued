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
	