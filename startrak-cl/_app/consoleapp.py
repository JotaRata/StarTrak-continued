import sys
from _process.protocols import Executor, Parser, STException
from _process import parsers as parser
from _process import executors as execs
from alias import LanguageMode
from streams import ConsoleInput, ConsoleOutput
import startrak
_PREFIXES = {'st': '[ST]: ', 'py' : '[PY]: ', 'sh' : '[SH]: ' }

class ConsoleApp:
	mode : LanguageMode
	_parser : Parser
	_exc : Executor
	_globals = {var:vars(startrak)[var] for var in dir(startrak) if not var.startswith('_')}

	def __init__(self, *args : str) -> None:
		self.input = ConsoleInput()
		self.output = ConsoleOutput(sys.stdout)
		self.index = 0
		self.cursor = 0
		self.set_mode('st')
		sys.stdout = self.output
	
	def set_mode(self, mode : LanguageMode):
		match mode:
			case 'py':
				self._parser = parser.PythonParser()
				self._exc = execs.PythonExcecutioner(ConsoleApp._globals)
			case 'sh':
				self._parser = parser.ShellParser()
				self._exc = execs.ShellExecutioner({})
			case 'st':
				self._parser = parser.StartrakParser()
				self._exc = execs.StartrakExecutioner(ConsoleApp._globals)
		self.mode = mode

	def process(self, string : str):
		try:
			data = self._parser.parse(string)
			self._exc.execute(data)
		except STException as e:
			print('Error:', e)
		except Exception as e:
			print('Python Error:', e)
		if self.mode != 'st':
			self.set_mode('st')