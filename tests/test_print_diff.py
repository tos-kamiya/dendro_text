import unittest

from io import StringIO

from dendro_text.commands import do_diff


class TestDoDiff(unittest.TestCase):
    def test_for_small_fragments(self):
        ldoc = ['a', 'b', 'c']
        rdoc = ['a', 'x', 'y', 'c']

        sio = StringIO()
        do_diff(ldoc, rdoc, write=sio.write, lbegend=('-<', '>'), rbegend=('+<', '>'))
        sio.seek(0)
        self.assertEqual(sio.read(), "a-<b>+<xy>c")

        tmp = ldoc; ldoc = rdoc; rdoc = tmp
        sio = StringIO()
        do_diff(ldoc, rdoc, write=sio.write, lbegend=('-<', '>'), rbegend=('+<', '>'))
        sio.seek(0)
        self.assertEqual(sio.read(), "a-<xy>+<b>c")

    def test_for_continuous_subs(self):
        ldoc = ['a', 'b', 'c', 'd']
        rdoc = ['a', 'x', 'y', 'd']

        sio = StringIO()
        do_diff(ldoc, rdoc, write=sio.write, lbegend=('-<', '>'), rbegend=('+<', '>'))
        sio.seek(0)
        self.assertEqual(sio.read(), "a-<bc>+<xy>d")

        tmp = ldoc; ldoc = rdoc; rdoc = tmp
        sio = StringIO()
        do_diff(ldoc, rdoc, write=sio.write, lbegend=('-<', '>'), rbegend=('+<', '>'))
        sio.seek(0)
        self.assertEqual(sio.read(), "a-<xy>+<bc>d")


if __name__ == "__main__":
    unittest.main()
