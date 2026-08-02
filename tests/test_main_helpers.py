import unittest
from contextlib import redirect_stderr
from io import StringIO

from dendro_text.main import (
    LabelNode,
    _init_distance_worker,
    calc_dld,
    convert_to_int_docs,
    gen_parser,
    select_neighbors,
    uniq,
)


class TestMainHelpers(unittest.TestCase):
    def test_uniq_preserves_first_occurrence_order(self):
        self.assertEqual(uniq(["a", "b", "a", "c", "b"]), ["a", "b", "c"])

    def test_convert_to_int_docs_is_deterministic(self):
        docs = [["beta", "alpha"], ["alpha", "gamma"]]
        idocs, word_to_index = convert_to_int_docs(docs)
        self.assertEqual(word_to_index, {"alpha": 1, "beta": 2, "gamma": 3})
        self.assertEqual(idocs, [[2, 1], [1, 3]])

    def test_convert_to_int_docs_handles_empty_documents(self):
        idocs, word_to_index = convert_to_int_docs([[], ["a"]])
        self.assertEqual(idocs, [[], [1]])
        self.assertEqual(word_to_index, {"a": 1})

    def test_calc_dld_returns_pair_and_distance(self):
        _init_distance_worker([[1, 2], [1, 3]], lambda left, right: 1)
        self.assertEqual(calc_dld((0, 1)), ((0, 1), 1))

    def test_select_neighbors_keeps_first_document_and_sorts_by_distance(self):
        idocs = [[1], [1, 2], [1, 2, 3], [4, 5, 6]]
        labels = [LabelNode("first"), LabelNode("near"), LabelNode("far"), LabelNode("different")]
        selected_docs, selected_labels = select_neighbors(idocs, labels, neighbors=2)

        self.assertEqual(selected_docs, [[1], [1, 2], [1, 2, 3]])
        self.assertEqual([label.format() for label in selected_labels], ["first", "near", "far"])

    def test_parser_accepts_supported_option_values(self):
        args = gen_parser().parse_args(
            [
                "--char-by-char",
                "--max-depth",
                "2",
                "--workers",
                "1",
                "--neighbors",
                "2",
                "--neighbor-list",
                "0",
                "--prep",
                "cat",
                "--no-numba",
                "input.txt",
            ]
        )

        self.assertTrue(args.char_by_char)
        self.assertEqual(args.max_depth, 2)
        self.assertEqual(args.workers, 1)
        self.assertEqual(args.neighbors, 2)
        self.assertEqual(args.neighbor_list, 0)
        self.assertEqual(args.prep, ["cat"])
        self.assertTrue(args.no_numba)

    def test_parser_rejects_multiple_tokenization_modes(self):
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                gen_parser().parse_args(["--char-by-char", "--line-by-line", "input.txt"])


class TestListingOutput(unittest.TestCase):
    def test_select_neighbors_does_not_mutate_inputs(self):
        idocs = [[1], [1, 2], [4]]
        labels = [LabelNode("first"), LabelNode("near"), LabelNode("far")]
        original_idocs = [doc[:] for doc in idocs]
        original_labels = [label.format() for label in labels]

        select_neighbors(idocs, labels, neighbors=1)

        self.assertEqual(idocs, original_idocs)
        self.assertEqual([label.format() for label in labels], original_labels)


if __name__ == "__main__":
    unittest.main()
