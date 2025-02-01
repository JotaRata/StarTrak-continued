import os
import sys
# os.environ['ST_SESSION_DISABLED'] = '1'
sys.path.append(os.getcwd())
from console.shell import ShellConsole

from source import list_command
import startrak


app = ShellConsole()