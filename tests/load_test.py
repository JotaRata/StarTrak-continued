import os
import unittest
from startrak.io import *
from startrak.types import *

paths = ["aefor4.fit", "aefor7.fit", "aefor16.fit", "aefor25.fit"]
dir = "./tests/sample_files/"

class FileLoadingTest(unittest.TestCase):
    
    def test_files_exist(self):
        for path in paths:
            self.assertTrue(os.path.isfile(dir + path), "Test files are not in " + dir)

    def test_load_single(self):
        info = load_file(dir + paths[0])
        self.assertEqual(info.path, dir + paths[0], "Paths don't match")
        self.assertTrue(info.header is not None and len(info.header) > 0, 'Header is null/empty')
        self.assertTrue({"BITPIX", "NAXIS", "SIMPLE"} <= info.header.keys(), 'Invalid header')

    def test_load_multiple(self):
        infos = list(load_folder(dir))
        self.assertEqual(len(paths), len(infos) , "Returned list mismatch")
        for i, info in enumerate(infos):
            self.assertIsInstance(info, FileInfo, "Object is not FileInfo")
            self.assertTrue(info.path is not None and len(info.path) > len(dir))
            self.assertTrue(info.header is not None and len(info.header) > 0, 'Header is null/empty')

if __name__ == "__main__":
    unittest.main()
