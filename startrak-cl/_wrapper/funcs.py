import os
import re
import startrak
from _wrapper import ReturnInfo, get_text, register, pos, key, opos, okey, name, text, obj, path, Helper
from _wrapper.base import highlighted_text, underlined_text, inverse_text
from _process.protocols import STException
from startrak.native import FileInfo, Star

@register('session', kw= [key('-new', str), key('-mode', str), key('-scan-dir', str), okey('--v', int, 0)])
def _GET_SESSION(helper : Helper):
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
def _CHANGE_DIR(helper : Helper):
	path = helper.get_arg(0)
	os.chdir(path)
	new_path = os.getcwd()
	helper.print(new_path)
	return ReturnInfo(os.path.basename(new_path), path= new_path)

@register('cwd')
@register('pwd')
def _GET_CWD(helper : Helper):
	path = os.getcwd().replace(r'\\', '/')
	helper.print(path)
	return ReturnInfo(os.path.basename(path), path= os.path.abspath(path), obj= path)

@register('ls', args= [opos(0, path)])
def _LIST_DIR(helper : Helper):
	if len(helper.args) == 0:
		path = os.getcwd()
	else:
		path = helper.get_arg(0)
	
	strgen = (os.path.basename(p) + ('/' if os.path.isdir(p) else '') for p in os.scandir(path))
	string = get_text('\n'.join, strgen)
	helper.print(string)
	return ReturnInfo(text= string, path= path)

@register('grep', args= [pos(0, str), pos(1, text)])
def _FIND_IN_TEXT(helper : Helper):
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
def _PRINT(helper : Helper):
	value = helper.get_arg(0)
	helper.print(value)
	return ReturnInfo(text= value, obj= value)

@register('open', args= [pos(0, path)], kw= [okey('--v', int, 0)])
def _LOAD_SESSION(helper : Helper):
	path = helper.get_arg(0)
	out, fold = helper.get_kw('--v')
	session = startrak.load_session(path)
	if out:
		helper.print(session.__pprint__(0, fold))
	return ReturnInfo(session.name, text= get_text(session.__pprint__, 0, fold if out else 4), obj= session)

@register('add', args= [pos(0, str), pos(1, path)], 
						kw= [okey('--v', int, 0), key('-pos', float, float), key('-ap', int)])
def _ADD_ITEM(helper : Helper):
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
def _GET_IETM(helper : Helper):
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
def _DEL_ITEM(helper : Helper):
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

@register('edit', args= [pos(0, str), pos(1, __int_or_str)])
def _EDIT_ITEM(helper : Helper):
	mode = helper.get_arg(0)
	index = helper.get_arg(1)

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
	
	def save_item(attrs : list[list[str, str]]):
		nonlocal item
		session = startrak.get_session()
		if mode == 'file':
			i = session.included_files._dict[item.name]
			session.included_files.remove(item)
			item = FileInfo.new(attrs[0][1])
			session.included_files.insert(i, item)
		if mode == 'star':
			i = session.included_stars._dict[item.name]
			session.included_stars.remove(item)
			pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
			pos = re.findall(pattern, attrs[1][1])
			item = Star(attrs[0][1],  tuple(float(p) for p in pos), int(attrs[2][1]), item.photometry)
			session.included_stars.insert(i, item)
	if mode == 'star':
		attrs = [
			['Name', item.name],
			['Position', f'{item.position.x} {item.position.y}'],
			['Aperture', str(item.aperture)],
			['Trackable', 'NA'],		#todo: make trackable a thing
			['Type', type(item).__name__],
		]
	elif mode == 'file':
		attrs = [
			['Path', item.path]
		]

	helper.save_buffer()
	line_edit = -1
	line_selected = -1
	escape = ''
	unsaved = False

	def on_action(key : str):
		nonlocal line_selected, line_edit, escape, unsaved
		output = ''
		rows, cols = os.get_terminal_size().lines, os.get_terminal_size().columns
		if line_edit != -2:
			if key == 'esc':
				line_selected = -1
				line_edit  = -2
				escape = ''
			if key == 'up' and line_selected > 0 and line_edit == -1:
				line_selected -= 1
			if key == 'down' and line_selected < len(attrs) - 1 and line_edit == -1:
				line_selected += 1
			if key == 'enter':
				if line_edit != line_selected:
					line_edit = line_selected
				else:
					line_edit = -1
			if line_edit >= 0 and (len(key) == 1 or key == 'space' or key == 'backspace'):
				unsaved = True
				if key == 'space':
					attrs[line_edit][1] += ' '
				elif key == 'backspace':
					attrs[line_edit][1] = attrs[line_edit][1][:-1]
				else:
					attrs[line_edit][1] += key
		else:
			if key == 'esc':
				line_selected = 0
				line_edit  = -1
			if key == 'enter':
				if escape == ':w':
					save_item(attrs)
					unsaved = False
					line_selected = 0
					line_edit  = -1
				elif escape == ':q':
					helper.retrieve_buffer()
					return True
				elif escape == ':wq':
					save_item(attrs)
					helper.retrieve_buffer()
					helper.print(f'Saved {mode}: {item.name}')
					return True
				else:
					line_selected = 0
					line_edit  = -1
			if len(key) == 1:
				escape += key

		if line_edit >= 0:
			footer = 'INSERT'
		elif line_edit == -1:
			footer = 'SELECT'
		elif line_edit == -2:
			footer = 'ESC ' + escape
		
		unsaved_flag = 'UNSAVED' if unsaved else ''
		header = f'Edit attributes for {mode}: "{item.name}"'
		output += (inverse_text(header + ' ' * (cols - len(header))) + '\n' * 4)
		indent = ' ' * 4
		for i, [key, value] in enumerate(attrs):
			if line_edit == i:
				line =  inverse_text(f'{key}:') + ' ' * (30 - len(key)) + inverse_text(f'{value}\n')
			elif line_selected == i:
				line = inverse_text(f'{key}:') + ' ' * (30 - len(key)) + underlined_text(f'{value}\n')
			else:
				line = f'{key}:' + ' ' * (30 - len(key)) + f'{value}\n'
			output += (indent + line)
		output += ('\n' * (rows - (5 + i + 2)))
		output += (inverse_text(footer + ' ' * (cols - len(footer) - len(unsaved_flag)) + unsaved_flag))

		helper.clear_console()
		helper.print(output, False)
		helper.flush_console()
		return False
	on_action('')
	helper.handle_action('', callbacks= [on_action])

@register('test')
def test(helper : Helper):
	helper.save_buffer()
	helper.clear_console()
	h_index = 0
	s_index = -1
	lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit".split()
	values = [''] *  len(lorem)
	
	def action(key):
		nonlocal h_index,s_index
		if key == 'enter':
			helper.retrieve_buffer()
			helper.print(f'You selected "{lorem[h_index]}"')
			return True
		
		if key == 'up':
			h_index -= 1
		if key == 'down':
			h_index += 1
		if key == 'tab':
			s_index = h_index
		if s_index != -1 and (len(key) == 1 or key == 'space' or key == 'backspace'):
			if key == 'space':
				values[s_index] += ' '
			elif key == 'backspace':
				values[s_index] = values[s_index][:-1]
			else:
				values[s_index] += key

		s = ''
		for i, _ in enumerate(lorem):
			if i == s_index:
				s += f' \033[47;30m{lorem[i]} = {values[i]}\033[0m\n'
			elif i == h_index:
				s += f'>{lorem[i]} = {values[i]}\n'
			else:
				s += f' {lorem[i]} = {values[i]}\n'
			
		helper.clear_console()
		print(s)
		# print(f'\033[{s_index + 1};0H\r')

		return False
	helper.handle_action('Select the word', callbacks= [action])
