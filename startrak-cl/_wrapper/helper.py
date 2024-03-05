from _process.protocols import STException
from _wrapper.base import _CommandInfo, Optional

class Helper:
	def __init__(self, command : _CommandInfo, args : list[str]) -> None:
		self.args = args
		self.command = command
	
	def get_kw(self, arg : str):
		types = self.command.keywords[arg]
		if len(self.args) < 1 + len(types): 
			return False
		if arg not in self.args: 
			return False
		idx = self.args.index(arg)
		if len(types) == 0:
			return True
		values = []
		for j, _type in enumerate(types, 1):
			next_ = self.args[idx + j]
			try:
				value = _type(next_)
			except:
				raise STException(f'Invalid argument type for "{self.command.name}" at position #{j}')
			values.append(value)
		if len(values) > 1:
			return values
		return value
			
	def get_arg(self, pos : int):
		_type = self.command.args[pos].type

		if pos > len(self.args):
			if type(self.command.args[pos]) is Optional:
					return None
			raise STException(f'Expected argument at position #{pos + 1} of the function "{self.command.name}"')
		try:
			value = _type(self.args[pos])
		except:
			print(pos, self.args, _type)
			raise STException(f'Invalid argument type for "{self.command.name}" at position #{pos + 1}')
		return value
