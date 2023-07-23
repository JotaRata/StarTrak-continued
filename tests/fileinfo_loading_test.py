import os
import unittest
from astropy.io import fits
from startrak.types import FileInfo

class FileInfoTest(unittest.TestCase):
    def test_FromHDU(self):
        path = "./tests/sample_files/aefor4.fit"
        hdu = fits.open(path)
        info = FileInfo.FromHDU(hdu)
        
        self.assertEqual(info.path, path)
        self.assertEqual(info.header, {})
        self.assertEqual(info.validated, True)

    def test_invalid_hdu(self):
        with self.assertRaises(TypeError):
            hdu = fits.HDUList()
            FileInfo.FromHDU(hdu)

if __name__ == "__main__":
    unittest.main()
