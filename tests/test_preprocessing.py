import unittest
import os.path as path
import tempfile

from dendro_text.commands import do_apply_preprocessors


script_dir = path.dirname(path.abspath(__file__))


class TestDoApplyPreProcessors(unittest.TestCase):
    def setUp(self):
        self.temp_dir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_preprocessor(self):
        tempd = self.temp_dir.name
        target_file = path.join(tempd, "input.txt")
        with open(target_file, "w") as outp:
            outp.write("a B c\n")
        preps = ["awk '{ print toupper($0) }'"]
        r = do_apply_preprocessors(preps, target_file, tempd)
        self.assertEqual(r, "A B C\n")

    def test_multiple_preprocessors(self):
        tempd = self.temp_dir.name
        target_file = path.join(tempd, "input.txt")
        with open(target_file, "w") as outp:
            outp.write("a B c\nd E f\n")
        preps = ["awk '{ print toupper($0) }'", "awk '/^A/'"]
        r = do_apply_preprocessors(preps, target_file, tempd)
        self.assertEqual(r, "A B C\n")


if __name__ == "__main__":
    unittest.main()
