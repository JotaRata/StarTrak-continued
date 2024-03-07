import os
import sys
# os.environ['ST_SESSION_DISABLED'] = '1'
sys.path.append(os.getcwd())

import startrak
from _app.shell import ShellConsole
app = ShellConsole()