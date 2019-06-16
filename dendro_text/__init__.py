import sys
from typing import *

import numpy as np
import scipy.spatial.distance as distance
from scipy.cluster.hierarchy import linkage, dendrogram
from docopt import docopt
import pygments.lexers
import pygments.token
import pygments.util
from pyxdameraulevenshtein import damerau_levenshtein_distance

from .print_tree import print_tree


LABEL_SEPARATOR = ','
LABEL_HEADER = '\t'


def text_split(text: str, filename: str) -> List[str]:
    try:
        lexer = pygments.lexers.get_lexer_for_filename(filename)
    except pygments.util.ClassNotFound:
        return text.split()
        
    tokens = lexer.get_tokens(text)
    words = []
    for t in tokens:
        token_type = t[0]
        token_str = t[1]
        if token_type in pygments.token.Text:
            pass
        elif token_type in pygments.token.String or token_type in pygments.token.Comment:
            words.extend(token_str.split())
        else:
            words.append(token_str)
    return words


Node = Union['LabelNode', List['Node']]
# Node = Union[LabelNode, List[Node]]  # Will someday become valid with `from __future__ import annotations`?


class LabelNode:
    def __init__(self, *items):
        self.items = list(items)
    
    def merge(self, other):
        self.items.extend(other.items)

    def format(self, label_separator=LABEL_SEPARATOR):
        return label_separator.join(self.items)


def extract_child_nodes(node: Node) -> Union[List[Node], None]:
    if isinstance(node, list):
        return node[:]
    else:
        return None


def gen_leaf_node_formatter(label_separator, label_header):
    def format_leaf_node(node: LabelNode) -> str:
        assert isinstance(node, LabelNode)
        return label_header + node.format(label_separator=label_separator)
    return format_leaf_node


__doc__ = """Draw dendrogram of similarity among text files.

Usage:
  dendro_text [options] <file>...
                
Options:
  -p --pyplot               Show graphical dendrogram with `matplotlib.pyplot`
  -m --max-depth=DEPTH      Flatten the subtrees deeper than this.
  -s --file-separator=S     File separator (default: tab).
  -f --field-separator=S    Separator of tree picture and file (default: tab).
"""


def main():
    args = docopt(__doc__)
    files = args['<file>']
    option_pyplot = args['--pyplot']
    option_max_depth = int(args['--max-depth'] or "0")
    option_file_separator = args['--file-separator']
    option_field_separator = args['--field-separator']
    if option_pyplot and option_max_depth:
        print("Options --pyplot and --max-depth are mutually exclusive.")
        return

    format_leaf_node = gen_leaf_node_formatter(
        option_file_separator or LABEL_SEPARATOR,
        option_field_separator or LABEL_HEADER)

    # read documents from files
    labels: List[LabelNode] = [LabelNode(f) for f in files]
    docs: List[List[str]] = []
    for f in files:
        with open(f, 'r') as inp:
            try:
                doc = inp.read()
            except:
                sys.exit('Error in reading a file: %s' % repr(f))
            words = text_split(doc, f)
            docs.append(words)

    # merge duplicated docs
    i = 0
    while i < len(docs):  # docs is modified inside the following loop
        j = i + 1
        while j < len(docs):
            if docs[j] == docs[i]:
                labels[i].merge(labels[j])
                del labels[j]
                del docs[j]
            else:
                j += 1
        i += 1

    # special case: just one file is given or all files are equivalent
    if len(docs) <= 1:
        if option_pyplot:
            print("All documents are equivalent to each other.")
        else:
            root_node = labels[0]
            print_tree(root_node, extract_child_nodes, format_leaf_node)
        return

    # do clustering of docs
    len_docs = len(docs)
    dmat = np.zeros([len_docs, len_docs])
    for i in range(len_docs):
        docsi = ' '.join(docs[i])
        for j in range(len_docs):
            dmat[i, j] = damerau_levenshtein_distance(docsi, ' '.join(docs[j])) if i < j else 0 if i == j else dmat[j, i]
    darr = distance.squareform(dmat)
    result = linkage(darr, method='average')
    # print(repr(result))  # for debug

    # plot clustering result as dendrogram
    if option_pyplot:
        import matplotlib.pyplot as plt
        plt.figure()
        label_strs = [label.format() for label in labels]
        dendrogram(result, labels=label_strs, orientation='right')
        # dendrogram(result, labels=[i for i in range(len_docs)], orientation='right')  # for debug
        plt.show()
    else:
        # make binary tree of labels
        index_to_node = labels[:]
        for li in result:
            left_i = int(li[0])
            right_i = int(li[1])
            n = [index_to_node[right_i], index_to_node[left_i]]
            index_to_node.append(n)
        root_node = n

        print_tree(root_node, extract_child_nodes, format_leaf_node, max_depth=option_max_depth)


if __name__ == '__main__':
    main()
