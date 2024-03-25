from io import StringIO
import os
import re
import threading
import time
import startrak
from base import Helper
from base.classes import highlighted_text, underlined_text, inverse_text
from processing.protocols import STException
from startrak.native import FileInfo, Star

def INTERACTIVE_ADD(helper : Helper, mode : str):
	if mode == 'star':
		item = Star('star', (0, 0))
	elif mode == 'file':
		item = FileInfo('', False, None, None)
	INTERACTIVE_EDIT(helper, mode, item, new= True)

def INTERACTIVE_LIST(helper : Helper, path : str):
	helper.save_buffer()
	paths = os.listdir(path)
	line_view = 0
	line_selected = -1
	def on_action(key : str):
		nonlocal line_selected, line_view
		h = helper.console.size()[0] - 1
		buffer = ''
		if key == 'up' and line_selected > 0:
			line_selected -= 1
			if line_selected < line_view:
				line_view = max(0, line_view - h)
		if key == 'down' and line_selected < len(paths) - 1:
			line_selected += 1
			if line_selected >= line_view + h:
				line_view = min(len(paths), line_view + h - 1)
		if key == 'enter':
			helper.retrieve_buffer()
			return True
		
		for i, p in enumerate(paths):
			if not (max(0, line_view) <= i < min(len(paths), line_view + h)):
				continue
			if i == line_selected:
				buffer += inverse_text(p)
			else:
				buffer += p
			
			buffer += '\n'
		helper.clear_console()
		helper.print(buffer, False)
		helper.flush_console()
		return False
	on_action('')
	helper.handle_action('', callbacks= [on_action])

def INTERACTIVE_EDIT(helper: Helper, mode : str, item, new = False):
	def save_item(attrs : list[list[str, str]]):
		nonlocal item
		session = startrak.get_session()
		if mode == 'file':
			if not new:
				i = session.included_files._dict[item.name]
				session.included_files.remove(item)
			else:
				i = len(session.included_files)
			item = FileInfo.new(attrs[0][1])
			session.included_files.insert(i, item)
		if mode == 'star':
			if not new:
				i = session.included_stars._dict[item.name]
				session.included_stars.remove(item)
			else:
				i = len(session.included_stars)
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
		rows, cols = helper.console.size()
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
					try:
						save_item(attrs)
						out = f'Saved {mode}: {item.name}'
					except:
						out = f'Failed to create {mode}'
					finally:
						helper.retrieve_buffer()
						helper.print(out)
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

def INTERACTIVE_SERVER(helper : Helper, server_out : StringIO):
	helper.save_buffer()
	mode = 0
	escape = ''

	def on_action(key : str):
		nonlocal mode, escape
		rows, cols = helper.console.size()
		buffer = StringIO()
		header = 'Startrak session server log'
		buffer.write(inverse_text(header + ' ' * (cols - len(header)) + '\n'))
		buffer.write('\n' * 2)

		lines = server_out.getvalue().split('\n')
		for line in lines:
			buffer.write(' ' + line + '\n')
		
		if key == 'esc':
			if mode == 0:
				mode = 1
			elif mode == 1:
				escape = ''
				mode = 0
			
		if mode == 1:
			if len(key) == 1:
				escape += key
			elif key == 'enter':
				if escape == ':q':
					return True
				mode = 0

		footer = 'READ' if mode == 0 else 'ESC ' + escape

		buffer.write('\n' * (rows - 4 - len(lines)))
		buffer.write(inverse_text(footer + ' ' * (cols - len(footer)) ))

		helper.clear_console()
		helper.print(buffer.getvalue(), False)
		helper.flush_console()
		
		return False
	
	def update_routine():
		ret = on_action('')
		while not ret:
			ret = on_action('')
			time.sleep(1)

	helper.handle_action('', callbacks= [on_action])
	threading.Thread(target= update_routine).start()