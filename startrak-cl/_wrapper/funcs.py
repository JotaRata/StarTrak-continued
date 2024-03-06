import os
import startrak
from _wrapper.base import register, Positional, Keyword, Optional
from _wrapper.helper import Helper
from _process.protocols import STException

@register('session', kw= [Keyword('-f', int), Keyword('-new', str), Keyword('-mode', str), Keyword('-scan-dir', str), Keyword('--v')])
def _GET_SESSION(command, args):
	helper = Helper(command, args)

	fold = helper.get_kw('-f')
	new = helper.get_kw('-new')
	if '-new' in args and not new:
		raise STException('Keyword "-new" expected argument: name')
	
	if new:
		mode = helper.get_kw('-mode')
		match mode:
			case False:
				s = startrak.new_session(new, 'inspect')
			case 'inspect' | 'insp' | 'InspectionSession':
				s = startrak.new_session(new, 'inspect')
			case 'scan' | 'ScanSession':
				_dir = helper.get_kw('-scan-dir')
				if not _dir:
					_dir = os.getcwd()
				s = startrak.new_session(new, 'scan', _dir)
			case _:
				raise STException(f'Unknown mode "{mode}"')

		out = helper.get_kw('--v')
		if out:
			startrak.pprint(s,  fold if fold else 1)
		return
	startrak.pprint(startrak.get_session(), fold if fold else 1)

@register('cd', args= [Positional(0, str)])
def _CHANGE_DIR(command, args):
	helper = Helper(command, args)
	path = helper.get_arg(0)
	os.chdir(path)
	print(os.getcwd())

@register('cwd')
@register('pwd')
def _GET_CWD(command, args):
	print(os.getcwd())


@register('ls', args= [Optional(0, str)])
def _LIST_DIR(command, args):
	helper = Helper(command, args)
	if len(args) == 0:
		path = os.getcwd()
	else:
		path = helper.get_arg(0)
	for path in os.scandir(path):
		print(os.path.basename(path) + ('/' if os.path.isdir(path) else ''))

@register('open', args= [Positional(0, str)], kw= [Keyword('-f', int)])
def _LOAD_SESSION(command, args):
	helper = Helper(command, args)
	path = helper.get_arg(0)
	out = helper.get_kw('--v')
	s = startrak.load_session(path)
	if out:
		fold = helper.get_kw('-f')
		startrak.pprint(s,  fold if fold else 1)

@register('add', args= [Positional(0, str), Positional(1, str)], 
						kw= [Keyword('--v'), Keyword('-f', int), Keyword('-pos', float, float), Keyword('-ap', int)])
def _ADD_ITEM(command, args):
	helper = Helper(command, args)
	mode = helper.get_arg(0)
	out = helper.get_kw('--v')
	if not startrak.get_session():
		raise STException('No session to add to, create one using "session -new"')
	match mode:
		case 'file':
			path = helper.get_arg(1)
			file = startrak.load_file(path, append= True)
			if out:
				fold = helper.get_kw('-f')
				startrak.pprint(file, fold if fold else 1)
		
		case 'star':
			name = helper.get_arg(1)
			if '-pos' not in args:
				raise STException('Missing required keyword: "-pos x y"')
			pos = helper.get_kw('-pos')
			apert = helper.get_kw('-ap')

			star = startrak.Star(name, pos, apert if apert else 16)
			startrak.add_star(star)

			if out:
				fold = helper.get_kw('-f')
				startrak.pprint(star, fold if fold else 1)

		case _:
			raise STException(f'Invalid argument: "{mode}", supported values are "file" and "star"')