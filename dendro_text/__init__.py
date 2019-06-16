import sys

import numpy as np
import scipy.spatial.distance as distance
from scipy.cluster.hierarchy import linkage, dendrogram
from docopt import docopt
import pygments.lexers
import pygments.token
import pygments.util
import Levenshtein


LABEL_SEPARATOR = ','
TREE_PICTURE_TABLE = {'L': '-+', 'M': '-+', 'R': ' `', 'l': ' |', 'm': ' |', 'r': '  ', 'p': '--'}
# TREE_PICTURE_TABLE = {'L': '\u2501\u2533', 'M': '\u2501\u254b', 'R': '\u3000\u2514', 'l': '\u3000\u2502', 'm': '\u3000\u2502', 'r': '\u3000\u3000', 'p': '\u2501\u2501'}


def text_split(text, filename):
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


def print_tree(node, child_nodes_extractor, leaf_formatter, file=sys.stdout):
    padding = TREE_PICTURE_TABLE['p']
    last_indent = []

    def print_tree_i(node, indent):
        cns = child_nodes_extractor(node)
        if cns is not None:
            for i, cn in enumerate(cns):
                if i == len(cns) - 1:
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
            file.write('%s%s %s\n' % ("".join(TREE_PICTURE_TABLE[pi] for pi in pic), padding, leaf_formatter(node)))
            # file.write('%s%s %s\n' % ("".join(pi for pi in pic), '', leaf_formatter(node)))  # for debug
            last_indent[:] = indent

    print_tree_i(node, [])


class LabelNode:
    def __init__(self, *items):
        self.items = list(items)
    
    def merge(self, other):
        self.items.extend(other.items)

    def format(self):
        return LABEL_SEPARATOR.join(self.items)


__doc__ = """Draw dendrogram of similarity among text files.

Usage:
  file_dendro [options] <file>...
                
Options:
  -p --pyplot   Show graphical dendrogram with `matplotlib.pyplot`
"""


def main():
    args = docopt(__doc__)
    files = args['<file>']
    option_pyplot = args['--pyplot']

    # read documents from files
    labels = [LabelNode(f) for f in files]
    docs = []
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

    # clustring docs
    len_docs = len(docs)
    dmat = np.zeros([len_docs, len_docs])
    for i in range(len_docs):
        for j in range(len_docs):
            if i <= j:
                dmat[i, j] = Levenshtein.distance(' '.join(docs[i]), ' '.join(docs[j]))
            else:
                dmat[i, j] = dmat[j, i]
    darr = distance.squareform(dmat)
    result = linkage(darr, method='average')
    # print(repr(result))  # for debug

    # plotting clustring results as dendrogram
    if option_pyplot:
        import matplotlib.pyplot as plt
        plt.figure()
        # dendrogram(result, labels=[i for i in range(len_docs)], orientation='right')
        label_strs = [label.format() for label in labels]
        dendrogram(result, labels=label_strs, orientation='right')
        plt.show()
    else:
        # make binay tree of labels
        index_to_node = labels[:]
        for li in result:
            left_i = int(li[0])
            right_i = int(li[1])
            n = [index_to_node[right_i], index_to_node[left_i]]
            index_to_node.append(n)
        root_node = n

        def child_nodes_extractor(node):
            if isinstance(node, list):
                return node[:]
            else:
                return None

        def leaf_formatter(node):
            assert isinstance(node, LabelNode)
            return node.format()
        
        print_tree(root_node, child_nodes_extractor, leaf_formatter)


if __name__ == '__main__':
    main()
