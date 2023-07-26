__unittest = True

import unittest 
from startrak.sessions import Session, SessionType
from startrak.internals.types import *

sessionName = 'Test Session'
testDir = '/test/'

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

# ------------- Test for exceptions ---------------
	def test_direct_ctor(self):
		with self.assertRaises(TypeError, msg= 'InspectionSession didnt fail'):
			session = InspectionSession()

		with self.assertRaises(TypeError, msg= 'ScanSession didnt fail'):
			session = ScanSession()

	def test_invalid_case(self):
		with self.assertRaises(TypeError):
			session = Session.Create('invalid')

if __name__ == '__main__':
		unittest.main()