from typing import List, Union

import os.path
import sys
import subprocess
import tempfile
from multiprocessing import Pool

import numpy as np
from docopt import docopt
import pygments.lexers
import pygments.token
import pygments.util
from pyxdameraulevenshtein import damerau_levenshtein_distance
from tqdm import tqdm

from .print_tree import print_tree, BOX_DRAWING_TREE_PICTURE_TABLE


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION'), 'r') as inp:
    __version__ = inp.read().strip()


def uniq(items):
    item_set = set()
    uis = []
    for i in items:
        if i not in item_set:
            uis.append(i)
            item_set.add(i)
    return uis


LABEL_SEPARATOR = ','
LABEL_HEADER = '\t'


def text_split(text: str, filename: str) -> List[str]:
    lexer = None
    try:
        lexer = pygments.lexers.get_lexer_for_filename(filename)
    except pygments.util.ClassNotFound:
        pass

    if lexer is None or filename.endswith('.txt'):  # lexer for '.txt' seems not working
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


class DummyProgressBar:
    def __init__(self):
        pass
    def update(self, value):
        pass
    def close(self):
        pass


def merge_duplicated_docs(docs, labels):
    docs = docs[:]
    labels = labels[:]
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
    return docs, labels


def select_neighbors(docs, labels, count_neighbors, progress=False):
    docs = docs[:]
    labels = labels[:]
    dds = [(0, 0)]
    docs0 = ' '.join(docs[0])
    pbar = tqdm(desc="Identifying neighbors", total=len(docs) - 1, leave=False) \
        if progress else DummyProgressBar()
    for i in range(1, len(docs)):
        d = damerau_levenshtein_distance(docs0, ' '.join(docs[i]))
        dds.append((d, i))
        pbar.update(1)
    pbar.close()
    dds.sort()
    dds = dds[:count_neighbors + 1]
    docs = [docs[i] for d, i in dds]
    labels = [labels[i] for d, i in dds]
    return docs, labels


def dld(i_j_doctexts):
    i, j, doctexts = i_j_doctexts
    return (i, j), damerau_levenshtein_distance(doctexts[i], doctexts[j])


def calc_dendrogram(docs, progress=False, files=None, workers=None):
    import scipy.spatial.distance as distance
    from scipy.cluster.hierarchy import linkage

    if workers is None:
        workers = 1

    len_docs = len(docs)
    doctexts = [' '.join(d) for d in docs]
    jobs = [(i, j, doctexts) for i in range(len_docs) for j in range(len_docs) if i < j]
    pbar = tqdm(desc="Building dendrogram", total=len(jobs), leave=False) \
        if progress else DummyProgressBar()
    dld_tbl = dict()
    try:
        with Pool(workers) as pool:
            for ij, v in pool.imap_unordered(dld, jobs):
                dld_tbl[ij] = v
                pbar.update(1)
    except KeyboardInterrupt as e:
        print("\nWarning: Stopped by Ctl+C. Show the results for now.", file=sys.stderr)
    pbar.close()

    dmat = np.zeros([len_docs, len_docs])
    for i in range(len_docs):
        for j in range(len_docs):
            if i < j:
                dmat[i, j] = dld_tbl[(i, j)]
            elif i == j:
                dmat[i, j] = 0
            else:
                assert i > j
                dmat[i, j] = dld_tbl[(j, i)]
    darr = distance.squareform(dmat)
    result = linkage(darr, method='average')
    return result


def print_dendrogram(result, labels, format_leaf_node, max_depth=0, tree_picture_table=None):
    index_to_node = labels[:]
    n = None
    for li in result:
        left_i = int(li[0])
        right_i = int(li[1])
        n = [index_to_node[right_i], index_to_node[left_i]]
        index_to_node.append(n)
    assert n is not None
    root_node = n

    print_tree(
        root_node, extract_child_nodes, format_leaf_node,
        max_depth=max_depth, tree_picture_table=tree_picture_table)


def pyplot_dendrogram(result, label_strs, font=None):
    from scipy.cluster.hierarchy import dendrogram
    import matplotlib.pyplot as plt
    if font:
        import matplotlib as mpl
        mpl.rcParams['font.family'] = font
    plt.figure()
    dendrogram(result, labels=label_strs, orientation='right')
    # dendrogram(result, labels=[i for i in range(len_docs)], orientation='right')  # for debug
    plt.show()


def do_listing_pyplot_font_names():
    import matplotlib.font_manager as fm
    font_names = list(set(f.name for f in fm.fontManager.ttflist))
    font_names.sort()
    print('\n'.join(font_names))


def do_listing_in_order_of_increasing_distance(
        labels: List[str], docs: List[List[str]],
        neighbors: int = -1, separator: str = '\t', progress: bool = False) -> None:
    dds = [(0, 0)]
    docs0 = ' '.join(docs[0])
    pbar = tqdm(desc="Identifying neighbors", total=len(docs) - 1, leave=False) \
        if progress else DummyProgressBar()
    for i in range(1, len(docs)):
        d = damerau_levenshtein_distance(docs0, ' '.join(docs[i]))
        dds.append((d, i))
        pbar.update(1)
    pbar.close()
    dds.sort()

    if neighbors > 0:
        dds = dds[:neighbors + 1]
    for dist, doci in dds:
        print("%d%s%s" % (dist, separator, labels[doci]))


def do_apply_preorocessors(preprocessors: List[str], target_file: str, temp_dir: str) -> str:
    if len(preprocessors) == 1:
        try:
            cmd = ' '.join([preprocessors[0], target_file])
            r = subprocess.check_output(cmd, shell=True)
            doc = r.decode('utf-8')
            return doc
        except Exception as e:
            sys.exit('Error in preprocessing a file: %s' % repr(target_file))
            raise e

    base_name = os.path.basename(target_file)
    tmp_file = os.path.join(temp_dir, base_name)
    with open(target_file, 'rb') as inp:
        tmp_file_content: bytes = inp.read()
    for prep in preprocessors:
        with open(tmp_file, 'wb') as outp:
            outp.write(tmp_file_content)
        try:
            cmd = ' '.join([prep, tmp_file])
            tmp_file_content = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            sys.exit('Error in preprocessing a file: %s' % repr(target_file))
            raise e
    doc = tmp_file_content.decode('utf-8')
    return doc


__doc__ = """Draw dendrogram of similarity among text files.

Usage:
  dendro_text [options] [-n NUM|-N NUM] [--prep=PREPROCESSOR]... <file>...
  dendro_text --pyplot-font-names
  dendro_text --version

Options:
  -l --line-by-line         Compare texts in a line-by-line manner.
  -p --pyplot               Plot dendrogram with `matplotlib.pyplot`
  -m --max-depth=DEPTH      Flatten the subtrees (of dendrogram) deeper than this.
  -n --neighbors=NUM        Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.
  -N --neighbor-list=NUM    List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.
  -s --file-separator=S     File separator (default: comma).
  -f --field-separator=S    Separator of tree picture and file (default: tab).
  -a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
  -j NUM                    Parallel execution. Number of worker processes.
  --prep=PREPROCESSOR       Perform preprocessing for each input file.
  --progress                Show progress bar with ETA.
  --pyplot-font-names       List font names can be used in plotting dendrogram.
  --pyplot-font=FONTNAME    Specify font name in plotting dendrogram.
"""


def main():
    args = docopt(__doc__, version="dendro_text %s" % __version__)
    files = args['<file>']
    option_line_by_line = args['--line-by-line']
    option_pyplot = args['--pyplot']
    option_max_depth = int(args['--max-depth'] or "0")
    option_neighbors = int(args['--neighbors'] or "0")
    option_neighbor_list = int(args['--neighbor-list'] or "-1")
    option_file_separator = args['--file-separator']
    option_field_separator = args['--field-separator']
    option_ascii_char_tree = args['--ascii-char-tree']
    option_progress = args['--progress']
    option_pyplot_font_names = args['--pyplot-font-names']
    option_pyplot_font = args['--pyplot-font']
    option_prep = args['--prep']
    option_workers = int(args['-j']) if args['-j'] else None
    if option_pyplot:
        if option_max_depth:
            sys.exit("Error: Options --pyplot and --max-depth are mutually exclusive.")
    else:
        if option_pyplot_font:
            sys.exit("Error: Option --pyplot-font is valid only with --pyplot.")

    if option_pyplot or option_pyplot_font_names:
        try:
            import matplotlib.pyplot as plt
        except ImportError as _e:
            sys.exit("Error: matplotlib.pyplot is not installed.")

    if option_pyplot_font_names:
        do_listing_pyplot_font_names()
        return

    format_leaf_node = gen_leaf_node_formatter(
        option_file_separator or LABEL_SEPARATOR,
        option_field_separator or LABEL_HEADER)

    tree_picture_table = BOX_DRAWING_TREE_PICTURE_TABLE if not option_ascii_char_tree else None

    files = uniq(files)

    def read_doc(f):
        if option_prep:
            doc = do_apply_preorocessors(option_prep, f, temp_dir.name)
        else:
            with open(f, 'r') as inp:
                try:
                    doc = inp.read()
                except Exception as _e:
                    sys.exit('Error in reading a file: %s' % repr(f))
        if option_line_by_line:
            words = doc.split()
        else:
            words = text_split(doc, f)
        return words

    # read documents from files
    temp_dir = tempfile.TemporaryDirectory() if option_prep else None
    labels: List[LabelNode] = [LabelNode(f) for f in files]
    docs = [read_doc(f) for f in files]
    if temp_dir is not None:
        temp_dir.cleanup()

    if option_neighbor_list != -1:
        # `list neighborsP command (option -N)
        label_strs = [label.format() for label in labels]
        do_listing_in_order_of_increasing_distance(
            label_strs, docs,
            neighbors=option_neighbor_list, separator=option_field_separator or LABEL_HEADER, progress=option_progress)
        return

    docs, labels = merge_duplicated_docs(docs, labels)

    # special case: just one file is given or all files are equivalent
    if len(docs) <= 1:
        if option_pyplot:
            print("All documents are equivalent to each other.")
        else:
            root_node = labels[0]
            print_tree(
                root_node, extract_child_nodes, format_leaf_node,
                tree_picture_table=tree_picture_table)
        return

    if option_neighbors > 0 and len(docs) > option_neighbors + 1:
        docs, labels = select_neighbors(docs, labels, option_neighbors, progress=option_progress)

    result = calc_dendrogram(docs, progress=option_progress, files=[ln.items[0] for ln in labels], workers=option_workers)
    # print(repr(result))  # for debug

    # plot clustering result as dendrogram
    if option_pyplot:
        label_strs = [label.format() for label in labels]
        pyplot_dendrogram(result, label_strs, font=option_pyplot_font)
    else:
        print_dendrogram(
            result, labels, format_leaf_node,
            max_depth=option_max_depth, tree_picture_table=tree_picture_table)


if __name__ == '__main__':
    main()
