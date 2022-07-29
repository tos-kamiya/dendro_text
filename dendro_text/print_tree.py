from typing import Callable, Dict, Iterator, List, Optional, TextIO, Tuple, TypeVar

import sys

ASCII_TREE_PICTURE_TABLE = {"L": "-+", "M": " +", "R": " `", "l": " |", "m": " |", "r": "  ", "p": "--"}

BOX_DRAWING_TREE_PICTURE_TABLE = {
    "L": "\u2500\u252c",
    "M": " \u251c",
    "R": " \u2514",
    "l": " \u2502",
    "m": " \u2502",
    "r": "  ",
    "p": "\u2500\u2500",
}

BOX_DRAWING_TREE_PICTURE_TABLE_W_FULLWIDTH_SPACE = {
    "L": "\u252c",
    "M": "\u251c",
    "R": "\u2514",
    "l": "\u2502",
    "m": "\u2502",
    "r": "\u3000",
    "p": "\u2500",
}

NodeType = TypeVar("NodeType")
LeafType = TypeVar("LeafType")


def print_tree(
    node: NodeType,
    child_nodes_extractor: Callable[[NodeType], Tuple[Optional[List[NodeType]], Optional[LeafType]]],
    leaf_node_formatter: Callable[[LeafType], str],
    max_depth: Optional[int] = None,  # no limit
    file: TextIO = sys.stdout,
    tree_picture_table: Optional[Dict[str, str]] = None,
):
    tpt: Dict[str, str] = tree_picture_table if tree_picture_table is not None else ASCII_TREE_PICTURE_TABLE

    if max_depth is None:
        max_depth = 0

    def collect_leaves_iter(node: NodeType) -> Iterator[LeafType]:
        cns, leaf = child_nodes_extractor(node)
        if cns is not None:
            for cn in cns:
                yield from collect_leaves_iter(cn)
        else:
            assert leaf is not None
            yield leaf

    padding = tpt["p"]
    last_indent = []

    def print_leaf(node, indent):
        pic = [""] * len(indent)
        for i in range(len(indent)):
            bi = indent[i]
            if i < len(last_indent) and bi == last_indent[i]:
                pic[i] = "l" if bi == 0 else "m" if bi > 0 else "r"
            else:
                pic[i] = "L" if bi == 0 else "M" if bi > 0 else "R"
        file.write("%s%s %s\n" % ("".join(tpt[pi] for pi in pic), padding, leaf_node_formatter(node)))
        # file.write('%s%s %s\n' % (''.join(pi for pi in pic), '', leaf_formatter(node)))  # for debug

    def print_tree_i(node, depth, indent):
        cns, leaf = child_nodes_extractor(node)
        if cns is not None:
            if depth == max_depth:
                cns = [cn for cn in collect_leaves_iter(node)]
                len_cns = len(cns)
                for i, cn in enumerate(cns):
                    if len_cns >= 2 and i == len_cns - 1:
                        i = -1
                    print_leaf(cn, indent + [i])
                    last_indent[:] = indent
            else:
                len_cns = len(cns)
                for i, cn in enumerate(cns):
                    if len_cns >= 2 and i == len_cns - 1:
                        i = -1
                    print_tree_i(cn, depth + 1, indent + [i])
        else:
            assert leaf is not None
            print_leaf(node, indent)
            last_indent[:] = indent

    print_tree_i(node, 1, [])


if __name__ == "__main__":
    node = ["a", ["b", "c"], ["d", "e", ["f"]]]

    def extract_child_nodes(node):
        if isinstance(node, list):
            return node[:], None
        else:
            return None, node  # the node is a leaf

    def format_leaf_node(node):
        return node

    print_tree(node, extract_child_nodes, format_leaf_node)
    print_tree(node, extract_child_nodes, format_leaf_node, max_depth=1)
