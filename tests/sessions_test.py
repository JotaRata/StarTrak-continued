__unittest = True

import unittest
from startrak.exceptions import InstantiationError 
from startrak.sessions import Session, SessionType
from startrak.internals.types import *
from startrak.io import *

sessionName = 'Test Session'
testDir = '/test/'

paths = ["aefor4.fit", "aefor7.fit", "aefor16.fit", "aefor25.fit"]
dir = "./tests/sample_files/"
class SessionTests(unittest.TestCase):

	def test_literal_eq(self):
		self.assertEqual(SessionType.ASTRO_INSPECT, 'inspect')
		self.assertEqual(SessionType.ASTRO_SCAN, 'scan')

	def test_ext_method(self):
		self.assertTrue(hasattr(Session, 'Create'))
# ------- Create sessions by using the extension method Session.Create

	def test_insp_session(self):
			session = Session.Create('inspect', sessionName)
			self.assertIs(type(session), InspectionSession)
			self.assertIsInstance(session, Session)
			self.assertEqual(session.name, sessionName)
		
	def test_scan_session(self):
		session = Session.Create('scan', sessionName, testDir)
		self.assertIs(type(session), ScanSession)
		self.assertIsInstance(session, Session)
		self.assertEqual(session.name, sessionName)
		self.assertEqual(session.working_dir, testDir)
	
	def test_inspect_tracked(self):
		session = Session.Create('inspect', sessionName)
		self.assertTrue(hasattr(session, 'tracked_items'))
	def test_scan_tracked(self):
		session = Session.Create('scan', sessionName, testDir)
		self.assertTrue(hasattr(session, 'tracked_items'))

	def test_session_load_file(self):
			s = Session.Create('inspect', 'Test session')
			s.add_item(load_file(dir + paths[0]))
			self.assertEqual(1, len(s.tracked_items))

	def test_session_load_folder(self):
			s = Session.Create('inspect', 'Test session')
			s.add_item(list(load_folder(dir)))
			self.assertEqual(len(paths), len(s.tracked_items))
# ------------- Test for exceptions ---------------
	def test_direct_ctor(self):
		with self.assertRaises(InstantiationError, msg= 'InspectionSession didnt fail'):
			session = InspectionSession()

		with self.assertRaises(InstantiationError, msg= 'ScanSession didnt fail'):
			session = ScanSession()

	def test_invalid_case(self):
		with self.assertRaises(TypeError):
			session = Session.Create('invalid', 'Invalid Session') # type: ignore

if __name__ == '__main__':
		unittest.main()