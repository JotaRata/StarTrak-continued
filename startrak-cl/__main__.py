import os
import sys

# os.environ['ST_SESSION_DISABLED'] = '1'
sys.path.append(os.getcwd())

import startrak
from startrak.native import Star

startrak.add_star(Star('test', (0,0)))
from _app.shell import ShellConsole
app = ShellConsole()