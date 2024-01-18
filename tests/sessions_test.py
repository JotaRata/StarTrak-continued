# type: ignore
__unittest = True


import unittest
from startrak.internals.exceptions import InstantiationError 
from startrak import *
from startrak.native import *
from startrak.io import *
from startrak.types.sessions import *

sessionName = 'Test Session'
testDir = '/test/'

paths = ["aefor4.fit", "aefor7.fit", "aefor16.fit", "aefor25.fit"]
dir = "./tests/sample_files/"
class SessionTests(unittest.TestCase):

# ------- Create sessions by using the extension method new_session

	def test_insp_session(self):
			session = new_session(sessionName, 'inspect', overwrite= True)
			self.assertIs(type(session), InspectionSession)
			self.assertIsInstance(session, Session)
			self.assertEqual(session.name, sessionName)
		
	def test_scan_session(self):
		session = new_session(sessionName, 'scan', testDir, overwrite= True)
		self.assertIs(type(session), ScanSession)
		self.assertIsInstance(session, Session)
		self.assertEqual(session.name, sessionName)
		self.assertEqual(session.working_dir, testDir)
	
	def test_inspect_tracked(self):
		session = new_session(sessionName, 'inspect', overwrite= True)
		self.assertTrue(hasattr(session, 'included_files'))
	def test_scan_tracked(self):
		session = new_session(sessionName, 'scan', testDir, overwrite= True)
		self.assertTrue(hasattr(session, 'included_files'))

	def test_session_load_file(self):
			s = new_session(sessionName, 'inspect', overwrite= True)
			s.add_file(load_file(dir + paths[0]))
			self.assertEqual(1, len(s.included_files))

	def test_session_load_folder(self):
			s = new_session(sessionName, 'inspect', overwrite= True)
			s.add_file( *load_folder(dir))
			self.assertEqual(len(paths), len(s.included_files))
# ------------- Test for exceptions ---------------
	def test_invalid_case(self):
		with self.assertRaises(NameError):
			session = new_session(sessionName, 'invalid', overwrite= True) # type: ignor, overwrite= Truee

if __name__ == '__main__':
		unittest.main()