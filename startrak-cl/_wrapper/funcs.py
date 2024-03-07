import os
import re
import startrak
from _wrapper.base import ReturnInfo, register, Positional, Keyword, Optional, name, text, obj
from _process.protocols import STException

@register('session', kw= [Keyword('-f', int), Keyword('-new', str), Keyword('-mode', str), Keyword('-scan-dir', str), Keyword('--v')])
def _GET_SESSION(helper):
	fold = helper.get_kw('-f')
	new = helper.get_kw('-new')
	if '-new' in helper.args and not new:
		raise STException('Keyword "-new" expected argument: name')
	
	session : startrak.native.Session
	session = startrak.get_session()
	if new:
		mode = helper.get_kw('-mode')
		match mode:
			case False:
				session = startrak.new_session(new, 'inspect')
			case 'inspect' | 'insp' | 'InspectionSession':
				session = startrak.new_session(new, 'inspect')
			case 'scan' | 'ScanSession':
				_dir = helper.get_kw('-scan-dir')
				if not _dir:
					_dir = os.getcwd()
				session = startrak.new_session(new, 'scan', _dir)
			case _:
				raise STException(f'Unknown mode "{mode}"')

		# todo: move printing logic outside of the functions
		out = helper.get_kw('--v')
		if out:
			startrak.pprint(session,  fold if fold else 1)
		return ReturnInfo(session.name, session.__pprint__(0, fold if fold else 1), session)
	else:
		if not session:
			raise STException('There is no session created, use the "-new" keyword to create one.')
		startrak.pprint(session, fold if fold else 1)
		return ReturnInfo(session.name, session.__pprint__(0, fold if fold else 1), session)

@register('cd', args= [Positional(0, text)])
def _CHANGE_DIR(helper):
	path = helper.get_arg(0)
	os.chdir(path)
	new_path = os.getcwd()
	helper.print(new_path)
	return ReturnInfo(os.path.basename(new_path), new_path)

@register('cwd')
@register('pwd')
def _GET_CWD(helper):
	path = os.getcwd().replace(r'\\', '/')
	helper.print(path)
	return ReturnInfo(os.path.basename(path), os.path.abspath(path))

@register('ls', args= [Optional(0, text)])
def _LIST_DIR(helper):
	if len(helper.args) == 0:
		path = os.getcwd()
	else:
		path = helper.get_arg(0)
	paths = []
	for path in os.scandir(path):
		paths.append(os.path.basename(path) + ('/' if os.path.isdir(path) else ''))
	string = '\n'.join(paths)
	helper.print(string)
	return ReturnInfo(path, string)

@register('grep', args= [Positional(0, str), Positional(1, text)])
def _FIND_IN_TEXT(helper):
	pattern = helper.get_arg(0)
	pattern = re.escape(pattern).replace(r'\*', r'.*?')
	try:
		path = helper.get_arg(1)
		with open(path, 'r') as file:
			lines = []
			for line in file:
				if re.search(pattern, line):
					lines.append(line)
	except (FileNotFoundError, OSError):
		text = helper.get_arg(1)
		lines = []
		for line in text.split('\n'):
			if re.search(pattern, line):
					lines.append(line)
	string = '\n'.join(lines)
	helper.print(string)
	single = lines[0] if len(lines) == 1 else None
	return ReturnInfo(single, string)

@register('echo', args= [Positional(0, text)])
def _PRINT(helper):
	value = helper.get_arg(0)
	helper.print(value)

@register('open', args= [Positional(0, name)], kw= [Keyword('--v'), Keyword('-f', int)])
def _LOAD_SESSION(helper):
	path = helper.get_arg(0)
	out = helper.get_kw('--v')
	session = startrak.load_session(path)
	fold = helper.get_kw('-f')
	if out:
		startrak.pprint(session,  fold if fold else 1)
	return ReturnInfo(session.name, session.__pprint__(0, fold if fold else 1), session)

@register('add', args= [Positional(0, str), Positional(1, name)], 
						kw= [Keyword('--v'), Keyword('-f', int), Keyword('-pos', float, float), Keyword('-ap', int)])
def _ADD_ITEM(helper):
	mode = helper.get_arg(0)
	out = helper.get_kw('--v')
	if not startrak.get_session():
		raise STException('No session to add to, create one using "session -new"')
	match mode:
		case 'file':
			path = helper.get_arg(1)
			file = startrak.load_file(path, append= True)
			fold = helper.get_kw('-f')
			if out:
				startrak.pprint(file, fold if fold else 1)
			return ReturnInfo(file.name, file.__pprint__(0, fold if fold else 1), file)
			return file.name
		
		case 'star':
			name = helper.get_arg(1)
			if '-pos' not in helper.args:
				raise STException('Missing required keyword: "-pos x y"')
			pos = helper.get_kw('-pos')
			apert = helper.get_kw('-ap')

			star = startrak.Star(name, pos, apert if apert else 16)
			startrak.add_star(star)

			fold = helper.get_kw('-f')
			if out:
				startrak.pprint(star, fold if fold else 1)
			return ReturnInfo(star.name, star.__pprint__(0, fold if fold else 1), star)
		case _:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')

def __int_or_str(value):
	if value.isdigit(): return int(value)
	else: return str(value)
@register('get', args= [Positional(0, str), Positional(1, __int_or_str)], kw= [Keyword('-f', int)])
def _GET_IETM(helper):
	mode = helper.get_arg(0)
	index = helper.get_arg(1)

	match mode:
		case 'file':
			item = startrak.get_file(index)
		case 'star':
			item = startrak.get_star(index)
		case _:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')
	fold = helper.get_kw('-f')
	startrak.pprint(item, fold if fold else 1)
	return ReturnInfo(item.name, item.__pprint__(0, fold if fold else 1), item)
	return item.name
