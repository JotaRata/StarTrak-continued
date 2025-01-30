# from inspect import currentframe, getframeinfo
# from contextlib import contextmanager
# import inspect
# from turtle import position


# class DebugContextManager:
# 	def __init__(self, string):
# 		self.string = string

# 	def __enter__(self):
# 		# before block
# 		frame = currentframe().f_back
# 		info = getframeinfo(frame)
# 		self.filename = info.filename
# 		self.first_line = info.positions.lineno
# 		print(self.first_line)

# 	def __exit__(self, exc_type, exc_value, traceback):
# 		# after block
# 		frame = currentframe().f_back
# 		info = getframeinfo(frame)

# 		self.last_line = info.positions.end_lineno

# 		with open(self.filename) as f:
# 			lines = f.readlines()[self.first_line:self.last_line]
		
# 		indent = len(lines[0]) - len(lines[0].lstrip())

# 		print('POSITIONS:', indent, info.positions.col_offset, info.positions.end_col_offset, info.positions.lineno)
# 		print(self.last_line)
# 		for line in lines:
# 			print(line[indent:].rstrip())


# def test():
# 		with DebugContextManager("show this code in stdout:"):
# 			a = 1
# 			b = 2
# 			a, b = b, a
# 			if False:
# 				print('done')
# 				if True:
# 					print('nein')

# test()
# print("DONE")


from commands import CommandBuilder, Parameter, register_command

command = register_command(
			CommandBuilder('test_command', "1.2.3")
				.add_author('Jota').add_description('Test Command')
				.add_parameter(Parameter('arg1')
							.with_type(int)
							.with_validation(lambda x: x > 0))
							)
with command.get_context() as exc:
	exc.print('Hello world')
	if True:
		exc.read()
		exc.print('Inner block')
	exc.print('Done')
	def s():
		pass

print('end', command._block_start, command._block_end)


with open(command._file_name, 'r') as file:
	lines = file.readlines()[command._block_start : command._block_end]
	for i, line in enumerate(lines):
		print(i, line.rstrip())