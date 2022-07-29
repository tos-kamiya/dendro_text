import unittest
import io

from dendro_text.print_tree import print_tree


def extract_child_nodes(node):
    if isinstance(node, list):
        return node[:], None
    else:
        return None, node  # the node is a leaf


def format_leaf_node(node):
    return node


class TestPrintTree(unittest.TestCase):
    def test_print_tree(self):
        node = ["a", ["b", "c"], ["d", "e", ["f"]]]
        buf = io.StringIO()
        print_tree(node, extract_child_nodes, format_leaf_node, file=buf)
        # print(buf.getvalue())
        self.assertEqual(buf.getvalue(), "-+-- a\n +-+-- b\n | `-- c\n `-+-- d\n   +-- e\n   `-+-- f\n")

    def test_print_tree_empty(self):
        node = []
        buf = io.StringIO()
        print_tree(node, extract_child_nodes, format_leaf_node, file=buf)
        # print(buf.getvalue())
        self.assertEqual(buf.getvalue(), "")

    def test_print_tree_single_leaf(self):
        node = ["a"]
        buf = io.StringIO()
        print_tree(node, extract_child_nodes, format_leaf_node, file=buf)
        # print(buf.getvalue())
        self.assertEqual(buf.getvalue(), "-+-- a\n")

    def test_print_tree_depth1(self):
        node = ["a", ["b", "c"], ["d", "e", ["f"]]]
        buf = io.StringIO()
        print_tree(node, extract_child_nodes, format_leaf_node, max_depth=1, file=buf)
        # print(buf.getvalue())
        self.assertEqual(buf.getvalue(), "-+-- a\n +-- b\n +-- c\n +-- d\n +-- e\n `-- f\n")

    def test_print_tree_depth2(self):
        node = ["a", ["b", "c"], ["d", "e", ["f"]]]
        buf = io.StringIO()
        print_tree(node, extract_child_nodes, format_leaf_node, max_depth=2, file=buf)
        # print(buf.getvalue())
        self.assertEqual(buf.getvalue(), "-+-- a\n +-+-- b\n | `-- c\n `-+-- d\n   +-- e\n   `-- f\n")


if __name__ == "__main__":
    unittest.main()
