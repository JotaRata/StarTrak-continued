import os
import re
import startrak
from _wrapper import ReturnInfo, register, pos, key, opos, okey, name, text, obj, path
from _process.protocols import STException

@register('session', kw= [key('-new', str), key('-mode', str), key('-scan-dir', str), okey('--v', int, 0)])
def _GET_SESSION(helper):
	new = helper.get_kw('-new')
	out, fold = helper.get_kw('--v')
	if '-new' in helper.args and not new:
		raise STException('key "-new" expected argument: name')
	session : startrak.native.Session
	session = startrak.get_session()
	out = (session is not None) | out
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
	else:
		if not session:
			raise STException('There is no session created, use the "-new" keyword to create one.')
	
	if out:
		helper.print(session.__pprint__(0, fold))
	return ReturnInfo(session.name, session.__pprint__(0, 4), session)

@register('cd', args= [pos(0, path)])
def _CHANGE_DIR(helper):
	path = helper.get_arg(0)
	os.chdir(path)
	new_path = os.getcwd()
	helper.print(new_path)
	return ReturnInfo(os.path.basename(new_path), path= new_path)

@register('cwd')
@register('pwd')
def _GET_CWD(helper):
	path = os.getcwd().replace(r'\\', '/')
	helper.print(path)
	return ReturnInfo(os.path.basename(path), path= os.path.abspath(path))

@register('ls', args= [opos(0, text)])
def _LIST_DIR(helper):
	if len(helper.args) == 0:
		path = os.getcwd()
	else:
		path = helper.get_arg(0)
	paths = []
	for p in os.scandir(path):
		paths.append(os.path.basename(p) + ('/' if os.path.isdir(p) else ''))
	string = '\n'.join(paths)
	helper.print(string)
	return ReturnInfo(text= string, path= path)

@register('grep', args= [pos(0, str), pos(1, text)])
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

@register('echo', args= [pos(0, text)])
def _PRINT(helper):
	value = helper.get_arg(0)
	helper.print(value)

@register('open', args= [pos(0, path)], kw= [okey('--v', int, 0)])
def _LOAD_SESSION(helper):
	path = helper.get_arg(0)
	out, fold = helper.get_kw('--v')
	session = startrak.load_session(path)
	if out:
		helper.print(session.__pprint__(0, fold))
	return ReturnInfo(session.name, session.__pprint__(0, 4), session)

@register('add', args= [pos(0, str), pos(1, path)], 
						kw= [okey('--v', int, 0), key('-pos', float, float), key('-ap', int)])
def _ADD_ITEM(helper):
	mode = helper.get_arg(0)
	out, fold = helper.get_kw('--v')
	if not startrak.get_session():
		raise STException('No session to add to, create one using "session -new"')
	match mode:
		case 'file':
			path = helper.get_arg(1)
			file = startrak.load_file(path, append= True)
			if out:
				helper.print(file.__pprint__(0, fold))
			return ReturnInfo(file.name, file.__pprint__(0, 4), file)
		
		case 'star':
			name = helper.get_arg(1)
			if '-pos' not in helper.args:
				raise STException('Missing required keyword: "-pos x y"')
			pos = helper.get_kw('-pos')
			apert = helper.get_kw('-ap')
			star = startrak.Star(name, pos, apert if apert else 16)
			startrak.add_star(star)
			if out:
				helper.print(star.__pprint__(0, fold))
			return ReturnInfo(star.name, star.__pprint__(0, 4), star)
		
		case _:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')

def __int_or_str(value):
	if value.isdigit(): return int(value)
	else: return str(value)
@register('get', args= [pos(0, str), pos(1, __int_or_str)], kw= [key('--v', int)])
def _GET_IETM(helper):
	mode = helper.get_arg(0)
	index = helper.get_arg(1)
	fold = helper.get_kw('--v')

	match mode:
		case 'file':
			item = startrak.get_file(index)
		case 'star':
			item = startrak.get_star(index)
		case _:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')
	
	helper.print(item.__pprint__(0, fold if fold else 0))
	return ReturnInfo(item.name, item.__pprint__(0, 4), item)
