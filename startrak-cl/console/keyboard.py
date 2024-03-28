import os
import sys
import threading
from typing import Any, Callable

if os.name == 'nt':
	import msvcrt

	def read_char():
		return msvcrt.getwch()

	def read_escape(char):
		return True if char in ("\x00", "à") else False

	def dump_keyboard():
		try:                      
			msvcrt.ungetwch("a")  
		except OSError:           
			return msvcrt.getwch()
		else:                     
			_ = msvcrt.getwch()   
			return ""

elif os.name == 'posix':
	import termios
	import tty

	def read_char():
		old_settings = termios.tcgetattr(sys.stdin.fileno())
		tty.setraw(sys.stdin.fileno())
		wchar = sys.stdin.read(1)
		termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, old_settings)
		return wchar

	def read_escape(char):
		return True if char == "\x1b" else False

	def dump_keyboard():
		old_settings = termios.tcgetattr(sys.stdin.fileno())
		tty.setraw(sys.stdin.fileno())
		os.set_blocking(sys.stdin.fileno(), False)
		buffer_dump = ""
		while char := sys.stdin.read(1):
			buffer_dump += char
		os.set_blocking(sys.stdin.fileno(), True)
		termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, old_settings)
		if buffer_dump:
			return buffer_dump
		else:
			return ""

__all__ = ['add_callback', 'remove_callback', 'normalize', 'listen']

KeyEvent = Callable[[str], Any]
_callbacks = list[KeyEvent]()

def add_callback(event : KeyEvent):
	_callbacks.append(event)

def remove_callback(event : KeyEvent):
	if event in _callbacks:
		_callbacks.remove(event)

def get_char():
	wchar = read_char()   
	if read_escape(wchar):  
		dump = dump_keyboard()
		return wchar + dump     
	else:                       
		return wchar

_NORM_MAP = {	b'\r' : 'enter',
					b' ' : 'space',
					b'\x08' : 'backspace',
					b'\x1b' : 'esc',
					b'\t' : 'tab',
					b'\xc3\xa0S' : 'del',
					b'\xc3\xa0R' : 'insert',
					b'\xc3\xa0H' : 'up',
					b'\xc3\xa0P' : 'down',
					b'\xc3\xa0K' : 'left',
					b'\xc3\xa0M' : 'right',
					# Unix keyboard
					b'\x1b[3~' : 'del',
					b'\x1b[2~' : 'insert',
					b'\x7f' : 'backspace',
					b'\x1b[A' : 'up',
					b'\x1b[B' : 'down',
					b'\x1b[D' : 'left',
					b'\x1b[C' : 'right',
					}
def normalize(char : bytes):
	if char in _NORM_MAP:
		return _NORM_MAP[char]
	return char.decode()


def listen():
	while True:
		char = get_char()
		norm = normalize(char.encode())
		for event in _callbacks:
			event(norm)
		
threading.Thread(target= listen).start()
