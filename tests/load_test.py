# type: ignore
import os
import unittest
from startrak.native import FileInfo, Header
from startrak.io import *

paths = ["aefor4.fit", "aefor7.fit", "aefor16.fit", "aefor25.fit"]
folder = "./tests/sample_files/"

class FileLoadingTest(unittest.TestCase):
    
    def test_files_exist(self):
        for path in paths:
            self.assertTrue(os.path.isfile(folder + path), "Test files are not in " + folder)

    def test_load_single(self):
        info = load_file(folder + paths[0])
        self.assertEqual(info.__path, os.path.abspath(folder + paths[0]), "Paths don't match")
        self.assertTrue(info.header is not None and isinstance(info.header, Header), 'Header is null/empty')
        self.assertTrue(info.header.contains_key("SIMPLE"), 'Invalid header')
        self.assertTrue(info.header.contains_key("BITPIX"), 'Invalid header')
        self.assertTrue(info.header.contains_key("NAXIS"), 'Invalid header')

    def test_load_multiple(self):
        infos = list(load_folder(folder))
        self.assertEqual(len(paths), len(infos) , "Returned list mismatch")
        for i, info in enumerate(infos):
            self.assertIsInstance(info, FileInfo, "Object is not FileInfo")
            self.assertTrue(info.__path is not None and len(info.__path) > len(folder))
            self.assertTrue(info.header is not None and isinstance(info.header, Header), 'Header is null/empty')
    
    # todo: Closed until immutable FileInfo is fixed
    # def test_fileinfo_immutability(self):
    #     f = load_file(folder + paths[0])
    #     try:
    #         f.path = 'Whatever'
    #     except AttributeError:
    #         return
    #     self.assertEqual(f.path, os.path.basename(paths[0]))
if __name__ == "__main__":
    unittest.main()
