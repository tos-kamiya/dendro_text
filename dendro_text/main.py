from itertools import count
from typing import Callable, List, Optional, Tuple, Union

import os.path
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
from docopt import docopt
from tqdm import tqdm
from init_attrs_with_kwargs import cast_set_attrs

from .dld import distance_list
from .print_tree import print_tree, BOX_DRAWING_TREE_PICTURE_TABLE, BOX_DRAWING_TREE_PICTURE_TABLE_W_FULLWIDTH_SPACE
from .ts import text_split, text_split_by_char_type
from .commands import DummyProgressBar, pyplot_dendrogram, do_listing_pyplot_font_names, do_apply_preorocessors, do_listing_in_order_of_increasing_distance


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"), "r") as inp:
    __version__ = inp.read().strip()


def uniq(items):
    item_set = set()
    uis = []
    for i in items:
        if i not in item_set:
            uis.append(i)
            item_set.add(i)
    return uis


LABEL_SEPARATOR = ","
LABEL_HEADER = "\t"


class LabelNode:
    def __init__(self, *items):
        self.items = list(items)

    def merge(self, other):
        self.items.extend(other.items)

    def format(self, label_separator=LABEL_SEPARATOR):
        return label_separator.join(self.items)


Node = Union[LabelNode, List["Node"]]


def extract_child_nodes(node: Node) -> Tuple[Optional[List[Node]], Optional[LabelNode]]:
    if isinstance(node, list):
        return node[:], None
    else:
        return None, node


def gen_leaf_node_formatter(label_separator: str, label_header: str) -> Callable[[LabelNode], str]:
    def format_leaf_node(node: LabelNode) -> str:
        assert isinstance(node, LabelNode)
        return label_header + node.format(label_separator=label_separator)

    return format_leaf_node


def merge_identical_docs(docs: List[List[str]], labels: List[LabelNode]) -> Tuple[List[List[str]], List[LabelNode]]:
    docs = docs[:]
    labels = labels[:]

    hash2indices = dict()
    for i, d in enumerate(docs):
        h = sum(hash(item) for item in d)
        hash2indices.setdefault(h, []).append(i)

    indice_set_tobe_removed = set()
    for h, indices in hash2indices.items():
        for i in range(len(indices)):
            idx1 = indices[i]
            if idx1 in indice_set_tobe_removed:
                continue  # for idx1
            for idx2 in indices[i + 1:]:
                if idx2 in indice_set_tobe_removed:
                    continue  # for idx2
                if docs[idx1] == docs[idx2]:
                    labels[idx1].merge(labels[idx2])
                    indice_set_tobe_removed.add(idx2)

    indices_tobe_removed = list(indice_set_tobe_removed)
    indices_tobe_removed.sort(reverse=True)
    for i in indices_tobe_removed:
        del docs[i]
        del labels[i]

    return docs, labels


def select_neighbors(docs: List[List[str]], labels: List[LabelNode], neighbors: int, progress: bool = False):
    docs = docs[:]
    labels = labels[:]
    dds: List[Tuple[int, int]] = [(0, 0)]
    pbar = tqdm(desc="Identifying neighbors", total=len(docs) - 1, leave=False) if progress else DummyProgressBar()
    for i in range(1, len(docs)):
        d = distance_list(docs[0], docs[i])
        dds.append((d, i))
        pbar.update(1)
    pbar.close()
    dds.sort()
    dds = dds[: neighbors + 1]
    docs = [docs[i] for d, i in dds]
    labels = [labels[i] for d, i in dds]
    return docs, labels


def calc_dld(i_j_docs):
    i, j, docs = i_j_docs
    return (i, j), distance_list(docs[i], docs[j])


def calc_dendrogram(docs, progress=False, workers=None):
    import scipy.spatial.distance as distance
    from scipy.cluster.hierarchy import linkage

    if workers is None:
        workers = 1

    len_docs = len(docs)
    jobs = [(i, j, docs) for i in range(len_docs) for j in range(len_docs) if i < j]
    pbar = tqdm(desc="Building dendrogram", total=len(jobs), leave=False) if progress else DummyProgressBar()
    dld_tbl = dict()
    try:
        with Pool(workers) as pool:
            for ij, v in pool.imap_unordered(calc_dld, jobs):
                dld_tbl[ij] = v
                pbar.update(1)
    except KeyboardInterrupt as _e:
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
    result = linkage(darr, method="average")
    return result


def print_dendrogram(result, labels, format_leaf_node, max_depth=None, tree_picture_table=None):
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
        root_node, extract_child_nodes, format_leaf_node, max_depth=max_depth, tree_picture_table=tree_picture_table
    )


class Args:
    file: List[str]
    tokenize: bool
    char_by_char: bool
    line_by_line: bool
    no_uniq_files: bool
    show_words: bool
    prep: List[str]
    max_depth: Optional[int]
    ascii_char_tree: bool
    box_drawing_tree_with_fullwidth_space: bool
    file_separator: Optional[str]
    field_separator: Optional[str]
    workers: Optional[int]
    progress: bool
    neighbors: Optional[int]
    neighbor_list: Optional[int]
    pyplot: bool
    pyplot_font_names: bool
    pyplot_font: Optional[str]
    version: str


__doc__ = """Draw dendrogram of similarity among text files.

Usage:
  dendro_text [options] [-c|-l|-t] [-n NUM|-N NUM] [-a|-B] [--prep=PREPROCESSOR]... <file>...
  dendro_text -W [-c|-l|-t] <file>
  dendro_text --pyplot-font-names
  dendro_text --version

Options:
  -t --tokenize             Compare texts as tokens of languages indicated by file extensions, using Pygments lexer.
  -c --char-by-char         Compare texts in a char-by-char manner.
  -l --line-by-line         Compare texts in a line-by-line manner.
  -U --no-uniq-files        Do not remove duplicates from the input files.
  -W --show-words           Show words extracted from the input file (No comparison is performed).
  --prep=PREPROCESSOR       Perform preprocessing for each input file.
  -m --max-depth=DEPTH      Flatten the subtrees (of dendrogram) deeper than this.
  -a --ascii-char-tree      Draw tree picture with ascii characters, not box-drawing characters.
  -B --box-drawing-tree-with-fullwidth-space    Draw tree picture with box-drawing characters and fullwidth space.
  -s --file-separator=S     File separator (default: comma).
  -f --field-separator=S    Separator of tree picture and file (default: tab).
  -j NUM --workers=NUM      Parallel execution. Number of worker processes.
  --progress                Show progress bar with ETA.
  -n --neighbors=NUM        Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.
  -N --neighbor-list=NUM    List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.
  -p --pyplot               Plot dendrogram with `matplotlib.pyplot`
  --pyplot-font-names       List font names can be used in plotting dendrogram.
  --pyplot-font=FONTNAME    Specify font name in plotting dendrogram.
"""


def main():
    docopt_args = docopt(__doc__, version="dendro_text %s" % __version__)
    args: Args = cast_set_attrs(Args(), **docopt_args)

    option_neighbor_list = args.neighbor_list if args.neighbor_list is not None else -1
    if args.pyplot:
        if args.max_depth is not None:
            sys.exit("Error: Options --pyplot and --max-depth are mutually exclusive.")
    else:
        if args.pyplot_font:
            sys.exit("Error: Option --pyplot-font is valid only with --pyplot.")

    if args.pyplot or args.pyplot_font_names:
        try:
            import matplotlib.pyplot as _plt
        except ImportError as _e:
            sys.exit("Error: matplotlib.pyplot is not installed.")

    if args.pyplot_font_names:
        do_listing_pyplot_font_names()
        return

    format_leaf_node = gen_leaf_node_formatter(
        args.file_separator or LABEL_SEPARATOR, args.field_separator or LABEL_HEADER
    )

    tree_picture_table = \
        BOX_DRAWING_TREE_PICTURE_TABLE_W_FULLWIDTH_SPACE if args.box_drawing_tree_with_fullwidth_space else \
        BOX_DRAWING_TREE_PICTURE_TABLE if not args.ascii_char_tree else \
        None

    files = args.file
    if not args.no_uniq_files:
        files = uniq(files)

    temp_dir = tempfile.TemporaryDirectory() if args.prep else None

    def read_doc(f):
        if args.prep:
            assert temp_dir is not None
            doc = do_apply_preorocessors(args.prep, f, temp_dir.name)
        else:
            with open(f, "r") as inp:
                try:
                    doc = inp.read()
                except Exception as _e:
                    sys.exit("Error in reading a file: %s" % repr(f))
        if args.char_by_char:
            words = [c for c in doc]
        elif args.line_by_line:
            words = doc.split("\n")
        elif args.tokenize:
            words = text_split(doc, f)
        else:
            words = text_split_by_char_type(doc)
        return words

    if args.show_words:
        for f in files:
            words = read_doc(f)
            for w in words:
                print(w)

    # read documents from files
    labels: List[LabelNode] = [LabelNode(f) for f in files]
    docs = [read_doc(f) for f in files]
    if temp_dir is not None:
        temp_dir.cleanup()

    if option_neighbor_list != -1:
        # `list neighborsP command (option -N)
        label_strs = [label.format() for label in labels]
        do_listing_in_order_of_increasing_distance(
            label_strs,
            docs,
            neighbors=option_neighbor_list,
            separator=args.field_separator or LABEL_HEADER,
            progress=args.progress,
        )
        return

    docs, labels = merge_identical_docs(docs, labels)

    # special case: just one file is given or all files are equivalent
    if len(docs) <= 1:
        if args.pyplot:
            print("All documents are equivalent to each other.")
        else:
            root_node = labels[0]
            print_tree(root_node, extract_child_nodes, format_leaf_node, tree_picture_table=tree_picture_table)
        return

    if args.neighbors is not None and args.neighbors > 0 and len(docs) > args.neighbors + 1:
        docs, labels = select_neighbors(docs, labels, args.neighbors, progress=args.progress)

    result = calc_dendrogram(docs, progress=args.progress, workers=args.workers)
    # print(repr(result))  # for debug

    # plot clustering result as dendrogram
    if args.pyplot:
        label_strs = [label.format() for label in labels]
        pyplot_dendrogram(result, label_strs, font=args.pyplot_font)
    else:
        print_dendrogram(
            result, labels, format_leaf_node, max_depth=args.max_depth, tree_picture_table=tree_picture_table
        )
