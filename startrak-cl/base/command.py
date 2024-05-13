
from dataclasses import dataclass
import os
import re
from typing import Callable, NamedTuple
sys.path.append(os.getcwd() + '/startrak-cl')

from io import StringIO
from types import CodeType
import startrak
import base
from base.interface import INTERACTIVE_ADD, INTERACTIVE_EDIT, INTERACTIVE_LIST, INTERACTIVE_SERVER
from processing.protocols import STException


EXEC_GLOBALS =  {'startrak.' + var : vars(startrak)[var] for var in dir(startrak)} |\
					{'os.' + var : vars(os)[var] for var in ['getcwd']} |\
					{var : vars(base)[var] for var in dir(base)} | {'STException' : STException}

SYMBOL_PATTERN = re.compile(r'\$([\w-]*\b|\d*\b)')

@dataclass(frozen= True)
class Command:
	name : str
	arguments : list[base.PositionalArg]
	keywords : list[base.KeywordArg]
	docstring : StringIO
	code : CodeType
	
	
	def __call__(self, helper : base.Helper):
		args = {'ARG_' + i : helper.get_arg(i) for i in range(len(self.arguments))}
		kws = {arg.key.replace('-','_').upper() : helper.get_kw(arg.key) for arg in self.keywords}
		
		locals = args | kws
		exec(self.code, EXEC_GLOBALS, locals)
		return locals.get('RETVAL', None)
	
	def __repr__(self) -> str:
		return f'{self.name} {" ".join(arg.kind for arg in self.arguments)}  {" ".join(arg.key for arg in self.keywords)}'

def load_definition(path : str) -> Command:
	# First pass: Read and parse file by sections
	with open(path, 'r') as f:
		status = -1
		header = ''
		body = StringIO()
		doc = StringIO()
		
		for line in f:
			if not line or line.startswith('#'):
				continue
			if 'import' in line:
				continue

			if status == -1:
				header = line
				status = 0
			else:
				if '<!BODY>' in line:
					status = 1
					continue
				if '<!DOC>' in line:
					status = 2
					continue
				if '<!END>' in line:
					status = 0
					continue
			
			if status == 1:
				if line.startswith('return'):
					line = line.replace('return', 'RETVAL = ')
				body.write(line)
			elif status == 2: 
				doc.write(line)
			elif status == 0:
				continue
			else:
				raise IOError('Invalid syntax in command definition.')
	body.seek(0)

	# Second pass: Extract definition from header
	name, *tokens = header.strip().split(' ')
	kws = list[str]()
	args = list[str]()
	for token in tokens:
		assert ':' in token, 'Invalid syntax in command header'
		key, kind, *extras = token.split(':')

		if key.startswith('$'):
			assert len(key) > 1, f'Missing index for token: {key}'
			args.append(base.Positional(int(key), kind))

		if key.startswith('&'):
			assert len(key) > 1, f'Missing index for token: {key}'
			args.append(base.Optional(int(key), kind))
		
		if key.startswith('-'):
			if len(extras) == 0:
				if '[' in kind and ']' in kind:
					kind = kind.strip('[]').split(',')
				kws.append(base.Keyword(key, kind))
			elif len(extras) == 1:
				kws.append(base.OptionalKeyword(key, kind, extras[0]))
			else:
				raise AssertionError('Invalid syntax')

	# Third pass: Format body tags
	offset = body.tell()
	for line in body:
		if '$' in line:
			match = SYMBOL_PATTERN.search(line)
			if not match:
				continue
			newline = line

			for group in match.groups():
				if group.isnumeric():
					newline = newline.replace('$'+ group, 'ARG_' + group)
				else:
					newline = newline.replace('$'+ group, group.replace('-', '_').upper())

			body.seek(offset)
			body.write(newline)
		offset = body.tell()

	code = compile(body.getvalue(), filename= name, mode= 'exec')
	return Command(name, arguments=args, keywords= kws, docstring= doc, code= code)

cmd = load_definition(r"C:\Users\jjbar\Documents\GitHub\StarTrak-continued\startrak-cl\base\commands\session.stc")