import sys
from typing import *
from typing.io import *


TREE_PICTURE_TABLE = {'L': '-+', 'M': ' +', 'R': ' `', 'l': ' |', 'm': ' |', 'r': '  ', 'p': '--'}
# TREE_PICTURE_TABLE = {'L': '\u2501\u2533', 'M': '\u3000\u254b', 'R': '\u3000\u2514', 'l': '\u3000\u2502', 'm': '\u3000\u2502', 'r': '\u3000\u3000', 'p': '\u2501\u2501'}


NodeType = TypeVar('NodeType')


def print_tree(
        node: NodeType,
        child_nodes_extractor: Callable[[NodeType], Union[List[NodeType], None]],
        leaf_node_formatter: Callable[[NodeType], str],
        file: TextIO = sys.stdout):
    padding = TREE_PICTURE_TABLE['p']
    last_indent = []

    def print_tree_i(node, indent):
        cns = child_nodes_extractor(node)
        if cns is not None:
            len_cns = len(cns)
            for i, cn in enumerate(cns):
                if len_cns >= 2 and i == len_cns - 1:
                    i = -1
                print_tree_i(cn, indent + [i])
        else:
            pic = [None] * len(indent)
            for i in range(len(indent)):
                bi = indent[i]
                if i < len(last_indent) and bi == last_indent[i]:
                    pic[i] = 'l' if bi == 0 else 'm' if bi > 0 else 'r'
                else:
                    pic[i] = 'L' if bi == 0 else 'M' if bi > 0 else 'R'
            file.write('%s%s %s\n' % ("".join(TREE_PICTURE_TABLE[pi] for pi in pic), padding, leaf_node_formatter(node)))
            # file.write('%s%s %s\n' % ("".join(pi for pi in pic), '', leaf_formatter(node)))  # for debug
            last_indent[:] = indent

    print_tree_i(node, [])


if __name__ == '__main__':
    node = ['a', ['b', 'c'], ['d', 'e', ['f']]]

    def extract_child_nodes(node):
        if isinstance(node, list):
            return node[:]
        else:
            return None  # the node is a leaf

    def format_leaf_node(node):
        return node

    print_tree(node, extract_child_nodes, format_leaf_node)
