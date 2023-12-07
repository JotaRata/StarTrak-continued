import os
import random
from startrak.io import import_stars, export_stars, load_file
from startrak.starutils import detect_stars
from startrak.native import Star, ReferenceStar
import unittest

STAR_NUM = 12
TEST_FITS = ('./tests/sample_files/aefor4.fit')
EXPORT_PATH = ('./tests/temp_data/output')
FILE_EXT = '.stlist'

class StarIOTests(unittest.TestCase):
	def test_star_creation(self):
		self.assertIsInstance(s := Star('Test', (0, 0), 1), Star)
		with self.subTest('Star Attributes'):
			self.assertEqual(s.name, 'Test')
			self.assertEqual(s.position, (0, 0))
			self.assertEqual(s.aperture, 1)
   
	# todo: Add method to create a star from a template
	# def test_star_inheritation(self):
	# 	self.assertIsInstance(s := Star('Test', (0, 0), 1), Star)
	# 	self.assertIsInstance(rs := ReferenceStar.From(s), ReferenceStar)
	# 	with self.subTest('Star Attributes'):
	# 		self.assertEqual(rs.name, 'Test')
	# 		self.assertEqual(rs.position, (0, 0))
	# 		self.assertEqual(rs.aperture, 1)
	# 		self.assertTrue(hasattr(rs, 'magnitude'))

	def test_star_export(self):
		if not os.path.isdir('./tests/temp_data'):
			os.mkdir('./tests/temp_data')
		ls= []
		with self.subTest('Multiple star creation'):
			try:
				for n in range(STAR_NUM):
					pos = random.randrange(-10, 10), random.randrange(-10, 10)
					apert = random.randrange(1, 20)
					if random.randint(0, 2) == 1:
						mag = random.randrange(10, 20)
						ls.append(ReferenceStar(f'RTest_{n}', pos, apert, None))
					else:
						ls.append(Star(f'Test_{n}', pos, apert, None))
			except:
				self.fail()
		with self.subTest('Export list of stars'):
			try:
				export_stars(EXPORT_PATH, ls)
			except Exception as e:
				self.fail(e)
			self.assertTrue(os.path.exists(EXPORT_PATH + FILE_EXT))
	
	# todo: Improve import logic
	# def test_star_import(self):
	# 	if not os.path.isdir('./tests/temp_data'): return
	# 	ls = None
	# 	with self.subTest('Import stars from file'):
	# 		try:
	# 			ls = list(import_stars(EXPORT_PATH + FILE_EXT))
	# 		except Exception as e:
	# 			self.fail(e)
		
	# 		self.assertIsNotNone(ls)
	# 		self.assertEqual(len(ls), STAR_NUM)
		
	def test_star_detection(self):
		img = None
		with self.subTest('File loading'):
			try:
				f = load_file(TEST_FITS)
				img = f.get_data()
			except Exception as e: self.fail(e)
		with self.subTest('Star Detection'):
			self.assertIsNotNone(img)
			try:
				s = detect_stars(img)
			except Exception as e: self.fail(e)
			self.assertEqual(len(s), 3)

if __name__ == '__main__':
	unittest.main()
	