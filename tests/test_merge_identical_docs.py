import unittest

from dendro_text.main import LabelNode, merge_identical_idocs


class TestMergeIdenticalDocs(unittest.TestCase):
    def test_no_identical_docs(self):
        docs = [
            [1, 2],
            [1],
            [2, 1],
        ]
        labels = [
            LabelNode("1"),
            LabelNode("2"),
            LabelNode("3"),
        ]

        mdocs, mlabels = merge_identical_idocs(docs, labels)

        self.assertCountEqual(mdocs, docs)
        for md, d in zip(mdocs, docs):
            self.assertSequenceEqual(md, d)

        self.assertCountEqual(mlabels, labels)
        for ml, l in zip(mlabels, labels):
            self.assertEqual(ml.format(), l.format())

    def test_identical_docs(self):
        docs = [
            [1, 2],
            [11],
            [1, 2],
            [21, 22],
            [11],
            [1, 2],
        ]
        labels = [
            LabelNode("1"),
            LabelNode("2"),
            LabelNode("3"),
            LabelNode("4"),
            LabelNode("5"),
            LabelNode("6"),
        ]

        mdocs, mlabels = merge_identical_idocs(docs, labels)

        labels_expected = [
            LabelNode("1,3,6"),
            LabelNode("2,5"),
            LabelNode("4"),
        ]
        docs_expected = [
            [1, 2],
            [11],
            [21, 22],
        ]

        self.assertEqual(len(mdocs), len(docs_expected))
        for md, d in zip(mdocs, docs_expected):
            self.assertSequenceEqual(md, d)

        self.assertEqual(len(mlabels), len(labels_expected))
        for ml, l in zip(mlabels, labels_expected):
            self.assertEqual(ml.format(), l.format())
