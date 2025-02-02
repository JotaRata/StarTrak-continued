import importlib.util
import os

from startrak_cl.processing.protocols import STException

SOURCE_PATH = 'startrak_cl/source/'
files = os.listdir(SOURCE_PATH)

for file in files:
	if file == '__init__.py':
		continue
	if not file.endswith('.py'):
		continue

	try:
		spec = importlib.util.spec_from_file_location(file.removesuffix('.py'), location= SOURCE_PATH + file)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
	except Exception as e:
		raise STException(f'Error while loading source file: {file}') from e