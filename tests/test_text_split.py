import unittest
from contextlib import redirect_stderr
from io import StringIO

from dendro_text.ts import normalize_block_name, strip_common_head_and_tail, text_split, text_split_by_char_type


class TestTextSplit(unittest.TestCase):
    def test_text_split_by_char_type(self):
        text = "文字の種類によってトークンに分割します。例えば、abcは別の単語になります。"
        doc = text_split_by_char_type(text)
        self.assertTrue("abc" in doc)
        self.assertTrue("種類" in doc)
        self.assertTrue("。" in doc)

    def test_unknown_lexer_falls_back_with_warning(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            doc = text_split("abc 123", "input.unknown-extension")

        self.assertEqual(doc, ["abc", " ", "123"])
        self.assertIn("Lexer not found for file", stderr.getvalue())


class TestStripCommonHeadAndTail(unittest.TestCase):
    def test_ht_short(self):
        lw = "  1 "
        rw = "  2 "
        h, t, l, r = strip_common_head_and_tail(lw, rw)

        self.assertEqual(h, "  ")
        self.assertEqual(t, " ")
        self.assertEqual(l, "1")
        self.assertEqual(r, "2")

        lw = "1 "
        rw = "  2"
        h, t, l, r = strip_common_head_and_tail(lw, rw)

        self.assertEqual(h, "")
        self.assertEqual(t, "")
        self.assertEqual(l, "1 ")
        self.assertEqual(r, "  2")


class TestNormalizeBlockName(unittest.TestCase):
    def test_names_with_suffixes(self):
        self.assertEqual(normalize_block_name("Latin Extended-A"), "Latin")
        self.assertEqual(normalize_block_name("Latin Extended-B"), "Latin")
        self.assertEqual(normalize_block_name("Miscellaneous Mathematical Symbols-A"), "Miscellaneous Mathematical Symbols")
        self.assertEqual(normalize_block_name("Supplemental Arrows-B"), "Supplemental Arrows")
        self.assertEqual(normalize_block_name("CJK Unified Ideographs Extension C"), "CJK Unified Ideographs")
        self.assertEqual(normalize_block_name("Phonetic Extensions"), "Phonetic")
        self.assertEqual(normalize_block_name("Phonetic Extensions Supplement"), "Phonetic")
