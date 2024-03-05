import sys
from _types.process.protocols import Executor, Parser, STException
from _types.process import parsers as parser
from _types.process import executors as execs
from _types.alias import LanguageMode
from _types.streams import ConsoleInput, ConsoleOutput
import startrak
_PREFIXES = {'st': '[ST]: ', 'py' : '[PY]: ', 'sh' : '[SH]: ' }

class ConsoleApp:
	mode : LanguageMode
	_parser : Parser
	_exc : Executor

	def __init__(self, *args : str) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.index = 0
		self.cursor = 0
		self.set_mode('st')
		sys.stdout = self.output
	
	def set_mode(self, mode : LanguageMode):
		_globals = {var:vars(startrak)[var] for var in dir(startrak) if not var.startswith('_')}
		match mode:
			case 'py':
				self._parser = parser.PythonParser()
				self._exc = execs.PythonExcecutioner(_globals)
			case 'sh':
				self._parser = parser.ShellParser()
				self._exc = execs.ShellExecutioner({})
			case 'st':
				self._parser = parser.StartrakParser()
				self._exc = execs.StartrakExecutioner(_globals)
		self.mode = mode

	def process(self, string : str):
		try:
			data = self._parser.parse(string)
			out = self._exc.execute(data)
			print(out)
		except STException as e:
			print('Error:', e)
		except Exception as e:
			print('Python Error:', e)
		if self.mode != 'st':
			self.set_mode('st')