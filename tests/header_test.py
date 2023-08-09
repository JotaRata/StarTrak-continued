# type: ignore
from startrak import *
from startrak.types import HeaderArchetype, Header
from startrak.io import *
import unittest

paths = ["aefor4.fit", "aefor7.fit", "aefor16.fit", "aefor25.fit"]
dir = "./tests/sample_files/"
class HeaderTest(unittest.TestCase):
		def test_header_from_file(self):
			f = load_file(dir + paths[0])
			self.assertIsInstance(f.header, Header)
		
		def test_get_from_header(self):
			f = load_file(dir + paths[0])
			self.assertIsNotNone(f.header['SIMPLE'])
		
		def test_archetype(self):
			f = load_file(dir + paths[0])
			arch = HeaderArchetype(f.header)
			self.assertIsInstance(arch, HeaderArchetype)

		def test_archetypes(self):
			f = load_file(dir + paths[0])
			arch = HeaderArchetype(f.header)
			
			for path in paths:
				s = load_file(dir + path)
				self.assertTrue(arch.validate(s.header))
		
		def test_session_archetype(self):
			s = new_session('inspect', 'Test session')
			s.add_item(list(load_folder(dir)))

			for f in s.included_items:
				self.assertTrue(s.archetype.validate(f.header))

if __name__ == '__main__':
	unittest.main()