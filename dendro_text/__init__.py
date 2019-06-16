import sys

import numpy as np
import scipy.spatial.distance as distance
from scipy.cluster.hierarchy import linkage, dendrogram
from docopt import docopt
import pygments.lexers
import pygments.token
import pygments.util
import Levenshtein

from .print_tree import print_tree


LABEL_SEPARATOR = ','


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

    # do clustering of docs
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

    # plot clustering results as dendrogram
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
