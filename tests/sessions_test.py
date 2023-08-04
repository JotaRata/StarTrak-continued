__unittest = True

import unittest
from startrak.internals.exceptions import InstantiationError 
from startrak import *
from startrak.types import *
from startrak.io import *

sessionName = 'Test Session'
testDir = '/test/'

paths = ["aefor4.fit", "aefor7.fit", "aefor16.fit", "aefor25.fit"]
dir = "./tests/sample_files/"
class SessionTests(unittest.TestCase):

	def test_literal_eq(self):
		self.assertEqual(SessionType.ASTRO_INSPECT, 'inspect')
		self.assertEqual(SessionType.ASTRO_SCAN, 'scan')

# ------- Create sessions by using the extension method create_session

	def test_insp_session(self):
			session = create_session('inspect', sessionName)
			self.assertIs(type(session), InspectionSession)
			self.assertIsInstance(session, Session)
			self.assertEqual(session.name, sessionName)
		
	def test_scan_session(self):
		session = create_session('scan', sessionName, testDir)
		self.assertIs(type(session), ScanSession)
		self.assertIsInstance(session, Session)
		self.assertEqual(session.name, sessionName)
		self.assertEqual(session.working_dir, testDir)
	
	def test_inspect_tracked(self):
		session = create_session('inspect', sessionName)
		self.assertTrue(hasattr(session, 'included_items'))
	def test_scan_tracked(self):
		session = create_session('scan', sessionName, testDir)
		self.assertTrue(hasattr(session, 'included_items'))

	def test_session_load_file(self):
			s = create_session('inspect', 'Test session')
			s.add_item(load_file(dir + paths[0]))
			self.assertEqual(1, len(s.included_items))

	def test_session_load_folder(self):
			s = create_session('inspect', 'Test session')
			s.add_item(list(load_folder(dir)))
			self.assertEqual(len(paths), len(s.included_items))
# ------------- Test for exceptions ---------------
	def test_invalid_case(self):
		with self.assertRaises(TypeError):
			session = create_session('invalid', 'Invalid Session') # type: ignore

if __name__ == '__main__':
		unittest.main()