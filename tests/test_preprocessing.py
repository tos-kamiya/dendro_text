import unittest
import io
import os.path as path
import sys
import tempfile

sys.path.insert(0, path.join(path.dirname(path.abspath(__file__)), '..'))

import dendro_text


script_dir = path.dirname(path.abspath(__file__))


class TestDoApplyPreorocessors(unittest.TestCase):
    def setUp(self):
        self.temp_dir = None
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        if self.temp_dir:
            self.temp_dir.cleanup()

    def test_single_preprocessor(self):
        tempd = self.temp_dir.name
        target_file = path.join(tempd, 'input.txt')
        with open(target_file, 'w') as outp:
            outp.write('a B c\n')
        preps = [
            "awk '{ print toupper($0) }'"
        ]
        r = dendro_text.do_apply_preorocessors(preps, target_file, tempd)
        self.assertEqual(r, "A B C\n")

    def test_multiple_preprocessors(self):
        tempd = self.temp_dir.name
        target_file = path.join(tempd, 'input.txt')
        with open(target_file, 'w') as outp:
            outp.write('a B c\nd E f\n')
        preps = [
            "awk '{ print toupper($0) }'",
            "awk '/^A/'"
        ]
        r = dendro_text.do_apply_preorocessors(preps, target_file, tempd)
        self.assertEqual(r, "A B C\n")


if __name__ == '__main__':
    unittest.main()