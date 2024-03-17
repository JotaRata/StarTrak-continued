import os
import re
import startrak
from _wrapper import ReturnInfo, get_text, register, pos, key, opos, okey, name, text, obj, path
from _process.protocols import STException

@register('session', kw= [key('-new', str), key('-mode', str), key('-scan-dir', str), okey('--v', int, 0)])
def _GET_SESSION(helper):
	new = helper.get_kw('-new')
	out, fold = helper.get_kw('--v')
	if '-new' in helper.args and not new:
		raise STException('key "-new" expected argument: name')
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
	else:
		if not session:
			raise STException('There is no session created, use the "-new" keyword to create one.')
	
	if out or (len(helper.args) == 0 and session is not None):
		helper.print(session.__pprint__(0, fold))
	return ReturnInfo(session.name, text= get_text(session.__pprint__, 0, fold if out else 4), obj= session)

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
	return ReturnInfo(os.path.basename(path), path= os.path.abspath(path), obj= path)

@register('ls', args= [opos(0, path)])
def _LIST_DIR(helper):
	if len(helper.args) == 0:
		path = os.getcwd()
	else:
		path = helper.get_arg(0)
	
	strgen = (os.path.basename(p) + ('/' if os.path.isdir(p) else '') for p in os.scandir(path))
	string = get_text('\n'.join, strgen)
	helper.print(string)
	return ReturnInfo(text= string, path= path)

@register('grep', args= [pos(0, str), pos(1, text)])
def _FIND_IN_TEXT(helper):
	pattern = helper.get_arg(0)
	pattern = re.escape(pattern).replace(r'\*', r'.*?')
	source = helper.get_arg(1)
	try:
		with open(source, 'r') as file:
			lines = []
			for line in file:
				if re.search(pattern, line):
					lines.append(line)
	except (FileNotFoundError, OSError):
		lines = []
		for line in source.split('\n'):
			if re.search(pattern, line):
					lines.append(line)
	string = '\n'.join(lines)
	helper.print(string)
	single = lines[0] if len(lines) == 1 else None
	return ReturnInfo(single, text= string, obj= single)

@register('echo', args= [pos(0, text)])
def _PRINT(helper):
	value = helper.get_arg(0)
	helper.print(value)
	return ReturnInfo(text= value, obj= value)

@register('open', args= [pos(0, path)], kw= [okey('--v', int, 0)])
def _LOAD_SESSION(helper):
	path = helper.get_arg(0)
	out, fold = helper.get_kw('--v')
	session = startrak.load_session(path)
	if out:
		helper.print(session.__pprint__(0, fold))
	return ReturnInfo(session.name, text= get_text(session.__pprint__, 0, fold if out else 4), obj= session)

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
			return ReturnInfo(file.name, text= get_text(file.__pprint__, 0, fold if out else 4), obj= file)
		
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
			return ReturnInfo(star.name, text= get_text(star.__pprint__, 0, fold if out else 4), obj= star)
		
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
	
	if index == '*':
		index = slice(None)

	match mode:
		case 'file':
			item = startrak.get_file(index)
		case 'star':
			item = startrak.get_star(index)
		case _:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')
	
	helper.print(item.__pprint__(0, fold if fold else 0))
	return ReturnInfo(getattr(item, 'name', None), text= get_text(item.__pprint__, 0, fold if fold else 4), obj= item)

# todo: add Y/N interactions with CLI
@register('del', args= [pos(0, str), pos(1, __int_or_str)], kw= [key('-f')])
def _DEL_ITEM(helper):
	mode = helper.get_arg(0)
	index = helper.get_arg(1)
	forced = helper.get_kw('-f')
	
	try:
		if mode == 'file':
			item = startrak.get_file(index)
		elif mode == 'star':
			item = startrak.get_star(index)
		else:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"') 
	except IndexError:
		raise STException(f'No {mode} with index: {index}') 
	except KeyError:
		raise STException(f'No {mode} with name: "{index}"') 

	def confirm(key):
		if key == 'n':
			return True
		if key == 'y':
			if mode == 'file':
				startrak.remove_file(item)
			elif mode == 'star':
				startrak.remove_star(item)
			helper.print(f'{item.name} deleted.')
			return True
		return False
	
	if not forced:
		helper.handle_action(f'Delete {mode}: {item.name}? (Y/N): ', callbacks= [confirm])
	else:
		confirm('y')
	return ReturnInfo(item.name, text= None, obj= None)
