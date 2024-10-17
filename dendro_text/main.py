from typing import Callable, List, Optional, Tuple, Union

import argparse
import os.path
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
from tqdm import tqdm

from .dld import distance_int_list
from .print_tree import print_tree, BOX_DRAWING_TREE_PICTURE_TABLE, BOX_DRAWING_TREE_PICTURE_TABLE_W_FULLWIDTH_SPACE
from .ts import text_split, text_split_by_char_type
from .commands import (
    DummyProgressBar,
    convert_to_int_docs,
    pyplot_dendrogram,
    do_listing_pyplot_font_names,
    do_apply_preprocessors,
    do_listing_in_order_of_increasing_distance,
    do_diff,
)


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


def merge_identical_idocs(idocs: List[List[int]], labels: List[LabelNode]) -> Tuple[List[List[int]], List[LabelNode]]:
    idocs = idocs[:]
    labels = labels[:]

    hash2indices = dict()
    for i, idoc in enumerate(idocs):
        h = sum(hash(idx) for idx in idoc)
        hash2indices.setdefault(h, []).append(i)

    indice_set_tobe_removed = set()
    for h, indices in hash2indices.items():
        for i in range(len(indices)):
            idx1 = indices[i]
            if idx1 in indice_set_tobe_removed:
                continue  # for idx1
            for idx2 in indices[i + 1 :]:
                if idx2 in indice_set_tobe_removed:
                    continue  # for idx2
                if idocs[idx1] == idocs[idx2]:
                    labels[idx1].merge(labels[idx2])
                    indice_set_tobe_removed.add(idx2)

    indices_tobe_removed = list(indice_set_tobe_removed)
    indices_tobe_removed.sort(reverse=True)
    for i in indices_tobe_removed:
        del idocs[i]
        del labels[i]

    return idocs, labels


def select_neighbors(
    idocs: List[List[int]], labels: List[LabelNode], neighbors: int, progress: bool = False
) -> Tuple[List[List[int]], List[LabelNode]]:
    idocs = idocs[:]
    labels = labels[:]
    dds: List[Tuple[int, int]] = [(0, 0)]
    pbar = tqdm(desc="Identifying neighbors", total=len(idocs) - 1, leave=False) if progress else DummyProgressBar()
    for i in range(1, len(idocs)):
        d = distance_int_list(idocs[0], idocs[i])
        dds.append((d, i))
        pbar.update(1)
    pbar.close()
    dds.sort()
    dds = dds[: neighbors + 1]
    idocs = [idocs[i] for d, i in dds]
    labels = [labels[i] for d, i in dds]
    return idocs, labels


def calc_dld(i_j_idocs):
    i, j, idocs = i_j_idocs
    return (i, j), distance_int_list(idocs[i], idocs[j])


def calc_dendrogram(idocs, progress=False, workers=None):
    import scipy.spatial.distance as distance
    from scipy.cluster.hierarchy import linkage

    if workers is None:
        workers = 1

    len_docs = len(idocs)
    jobs = [(i, j, idocs) for i in range(len_docs) for j in range(len_docs) if i < j]
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


def gen_parser():
    parser = argparse.ArgumentParser(
        description="Draw dendrogram of similarity among text files."
    )

    # Positional argument for <file>...
    parser.add_argument(
        'files', nargs='*', help='Input text files to compare.'
    )

    # Mutually exclusive options for -c, -l, -t
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-t', '--tokenize', action='store_true',
        help='Compare texts as tokens of languages indicated by file extensions, using Pygments lexer.'
    )
    group.add_argument(
        '-c', '--char-by-char', action='store_true',
        help='Compare texts in a char-by-char manner.'
    )
    group.add_argument(
        '-l', '--line-by-line', action='store_true',
        help='Compare texts in a line-by-line manner.'
    )

    # Other options
    parser.add_argument(
        '-U', '--no-uniq-files', action='store_true',
        help='Do not remove duplicates from the input files.'
    )
    parser.add_argument(
        '-d', '--diff', action='store_true',
        help='Diff mode (Implies option -U). **Experimental.**'
    )
    parser.add_argument(
        '-W', '--show-words', action='store_true',
        help='Show words extracted from the input file.'
    )
    parser.add_argument(
        '--prep', action='append', metavar='PREPROCESSOR',
        help='Perform preprocessing for each input file.'
    )
    parser.add_argument(
        '-m', '--max-depth', type=int, metavar='DEPTH',
        help='Flatten the subtrees (of dendrogram) deeper than this.'
    )
    parser.add_argument(
        '-a', '--ascii-char-tree', action='store_true',
        help='Draw tree picture with ascii characters, not box-drawing characters.'
    )
    parser.add_argument(
        '-B', '--box-drawing-tree-with-fullwidth-space', action='store_true',
        help='Draw tree picture with box-drawing characters and fullwidth space.'
    )
    parser.add_argument(
        '-s', '--file-separator', metavar='S', default=',',
        help='File separator (default: comma).'
    )
    parser.add_argument(
        '-f', '--field-separator', metavar='S', default='\t',
        help='Separator of tree picture and file (default: tab).'
    )
    parser.add_argument(
        '-j', '--workers', type=int, metavar='NUM',
        help='Parallel execution. Number of worker processes.'
    )
    parser.add_argument(
        '--progress', action='store_true',
        help='Show progress bar with ETA.'
    )
    parser.add_argument(
        '-n', '--neighbors', type=int, metavar='NUM',
        help='Pick up NUM (>=1) neighbors of (files similar to) the first file. Drop the other files.'
    )
    parser.add_argument(
        '-N', '--neighbor-list', type=int, metavar='NUM',
        help='List NUM neighbors of the first file, in order of increasing distance. `0` for +inf.'
    )
    parser.add_argument(
        '-p', '--pyplot', action='store_true',
        help='Plot dendrogram with `matplotlib.pyplot`.'
    )
    parser.add_argument(
        '--pyplot-font-names', action='store_true',
        help='List font names that can be used in plotting dendrogram.'
    )
    parser.add_argument(
        '--pyplot-font', metavar='FONTNAME',
        help='Specify font name in plotting dendrogram.'
    )
    parser.add_argument(
        '--version', action='version', version="dendro-text %s" % __version__,
        help='Show program\'s version number and exit.'
    )

    return parser


def main():
    parser = gen_parser()
    args = parser.parse_args()
    if not args.files:
        parser.print_help()
        return

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
            sys.exit("Error: matplotlib.pyplot has not been installed.")

    if args.pyplot_font_names:
        do_listing_pyplot_font_names()
        return

    format_leaf_node = gen_leaf_node_formatter(
        args.file_separator or LABEL_SEPARATOR, args.field_separator or LABEL_HEADER
    )

    tree_picture_table = (
        BOX_DRAWING_TREE_PICTURE_TABLE_W_FULLWIDTH_SPACE
        if args.box_drawing_tree_with_fullwidth_space
        else BOX_DRAWING_TREE_PICTURE_TABLE
        if not args.ascii_char_tree
        else None
    )

    files = args.files
    if not (args.diff or args.no_uniq_files):
        files = uniq(files)

    temp_dir = tempfile.TemporaryDirectory() if args.prep else None

    def read_doc(f):
        if args.prep:
            assert temp_dir is not None
            doc = do_apply_preprocessors(args.prep, f, temp_dir.name)
        else:
            with open(f, "r") as inp:
                try:
                    doc = inp.read()
                except Exception as e:
                    sys.exit("Error in reading a file: %s\n%s" % (repr(f), e))
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
        return

    # read documents from files
    labels: List[LabelNode] = [LabelNode(f) for f in files]
    docs = [read_doc(f) for f in files]
    if temp_dir is not None:
        temp_dir.cleanup()

    if args.diff:
        if len(docs) != 2:
            sys.exit("Error: Option -d requires exactly two files.")
        do_diff(docs[0], docs[1], sep='\n' if args.line_by_line else '')
        return

    idocs, _word_to_index = convert_to_int_docs(docs)

    if option_neighbor_list != -1:
        label_strs = [label.format() for label in labels]
        do_listing_in_order_of_increasing_distance(
            label_strs,
            idocs,
            neighbors=option_neighbor_list,
            separator=args.field_separator or LABEL_HEADER,
            progress=args.progress,
        )
        return

    # merge identical docs
    idocs, labels = merge_identical_idocs(idocs, labels)

    # special case: just one file is given or all files are equivalent
    if len(idocs) <= 1:
        if args.pyplot:
            print("All documents are equivalent to each other.")
        else:
            root_node = labels[0]
            print_tree(root_node, extract_child_nodes, format_leaf_node, tree_picture_table=tree_picture_table)
        return

    if args.neighbors is not None and args.neighbors > 0 and len(idocs) > args.neighbors + 1:
        idocs, labels = select_neighbors(idocs, labels, args.neighbors, progress=args.progress)

    result = calc_dendrogram(idocs, progress=args.progress, workers=args.workers)
    # print(repr(result))  # for debug

    # plot clustering result as dendrogram
    if args.pyplot:
        label_strs = [label.format() for label in labels]
        pyplot_dendrogram(result, label_strs, font=args.pyplot_font)
    else:
        print_dendrogram(
            result, labels, format_leaf_node, max_depth=args.max_depth, tree_picture_table=tree_picture_table
        )
