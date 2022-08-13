import unittest

from dendro_text.ts import text_split_by_char_type, strip_common_head_and_tail


class TestTextSplit(unittest.TestCase):
    def test_text_split_by_char_type(self):
        text = "文字の種類によってトークンに分割します。例えば、abcは別の単語になります。"
        doc = text_split_by_char_type(text)
        self.assertTrue("abc" in doc)
        self.assertTrue("種類" in doc)
        self.assertTrue("。" in doc)


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
