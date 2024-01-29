from contextlib import contextmanager
from pathlib import Path
import re
from typing import cast
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader, loadUiType
from PySide6.QtCore import QFile, QIODevice

BASE_DIR = Path(__file__).parent.parent
STUI_DIR = BASE_DIR / 'layouts/'
STSS_DIR = BASE_DIR / 'stylesheets/'


@contextmanager
def load_layout(name : str):
	ui_file = QFile( str(STUI_DIR / name) + '.ui')
	try:
		ui_file.open(QIODevice.OpenModeFlag.ReadOnly)
		yield ui_file
	except RuntimeError:
		print('Invalid path', str(STUI_DIR / name) + '.ui')
	finally:
		ui_file.close()

def load_class(name : str):
	ui_file = str(STUI_DIR / name) + '.ui'
	return cast(tuple[type, type], loadUiType(ui_file))

def load_style(name : str):
	ui_file = str(STSS_DIR / name) + '.qss'
	invalid_syntax = Exception('Invalid syntax')
	stylesheet = ''
	with open(ui_file, 'r') as file:
		# Block posidion code:
		# Its used to make sure the syntax is consistent with the rest of the file (I know there are better ways)
		root_block = 0	# 0= No parsing done yet
		variables = dict[str, str]()	# Create an empty dictionary to store the variables

		for line in file:
			if ':root' in line:
				root_block = 1 		# 1= :root label found, expecting opening bracket
			if '{' in line:
				if root_block == 1:
					root_block = 2 	# 2= opening brakcet found, the block is "safe" to read
					continue
				else:
					raise invalid_syntax
			if '}' in line:			# If the closing bracket is found, check the opening bracket has been found first
				if root_block != 2:	# If not the case, throw an error
					raise invalid_syntax
				# Else we reached the end of the block and the rsulting stylesheet is the rest of the file from this point
				else:
					stylesheet = file.read()
					break
			# If its safe to read, then split the key, values by a colon
			if root_block == 2:
				split = line.split(':')

				# Using match/case since its cool; store the variable in the dict
				match split:
					case  [key, value]:
						variables[key.strip()] = value.strip()
					case _:
						raise invalid_syntax
	
	# This pattern uses a logical OR to capture the words in the brackets
	# The dictionary keys are sorted in reversed since the regex engine only captures the first occurence
	# If p.e. "primary" is set before "primary-dark" then it will only capture "primary" 
	pattern = re.compile('@(' + '|'.join(sorted(variables, key= len, reverse=True)).strip('|') + ')')
	# Replace each match with the value of the variables dictionary (group 0 is a match that contains the @)
	stylesheet = pattern.sub(lambda match: variables[match.group(1)], stylesheet)
	return stylesheet
	
def create_widget(ui_file : QFile):
	loader = QUiLoader()
	return loader.load(ui_file, None)
