import os
import re
import startrak
from _wrapper import Helper
from _wrapper.base import underlined_text, inverse_text
from _process.protocols import STException
from startrak.native import FileInfo, Star

def INTERACTIVE_EDIT(mode : str, item):
	
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