import glob
import os

def path(ret : str):
	value : list[str]
	if type(ret) is str:
		if '*' in ret:
			value = glob.glob(ret, root_dir= os.getcwd() + '/')
		else:
			value = [ret]
	elif isinstance(ret, (list, tuple)):
		value = [str(item) for item in ret]
	else:
		return None
	if os.name == 'nt':
		value = [item.replace(r'\\', '/') for item in value]
	return value