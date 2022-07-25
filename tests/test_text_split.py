import unittest

from dendro_text.ts import text_split_by_char_type


class TestTextSplit(unittest.TestCase):
    def test_text_split_by_char_type(self):
        text = "文字の種類によってトークンに分割します。例えば、abcは別の単語になります。"
        doc = text_split_by_char_type(text)
        self.assertTrue("abc" in doc)
        self.assertTrue("種類" in doc)
        self.assertTrue("。" in doc)
