import os
import random
from startrak.io import load_file
from startrak.starutils import detect_stars
from startrak.native import Star, ReferenceStar, StarList
import unittest

from startrak.types.exporters import TextExporter
from startrak.types.importers import TextImporter

STAR_NAMES = ['Sirius', 'Vega', 'Rigel', 'Betelgeuse']
TEST_FITS = ('./tests/sample_files/aefor4.fit')
EXPORT_PATH = './tests/temp_data/stars.txt'
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

	def test_io(self):
		with self.subTest('Star creation'):
			try:
				star_list = StarList()
				for name in STAR_NAMES:
					position = random.randint(0, 640), random.randint(0, 480)
					aperture = random.randint(8, 16)
					if name == 'Vega':
						star = ReferenceStar(name, position, aperture)
						star.magnitude = 0.0
					else:
						star = Star(name, position, aperture)
					star_list.append(star)
			except Exception as e:
				self.fail(f'Star creation failed with error:\n{e}')
		
		with self.subTest('Star export'):
			try:
				with TextExporter(EXPORT_PATH) as out:
					out.write(star_list)
			except Exception as e:
				self.fail(f'Star list export failed: {e}')
		
		with self.subTest('Star import'):
			try:
				self.assertTrue(os.path.isfile(EXPORT_PATH), 'File doesnt exist')
				with TextImporter(EXPORT_PATH) as imp:
					obj = imp.read()
					print('Import sucessful')
			except Exception as e:
				self.fail(f'Star list import failed: {e}')
		
		with self.subTest('Verification'):
			self.assertIsInstance(obj, StarList)
			self.assertEqual(len(obj), len(STAR_NAMES))
			self.assertIsInstance(obj[0], Star)
			
			for i, star in enumerate(obj):
				self.assertEqual(star.name, STAR_NAMES[i])

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
	