from contextlib import nullcontext
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Union

import argparse
import os.path
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
from tqdm import tqdm

from .dld import distance_int_list, distance_int_list_python
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


@dataclass(frozen=True, init=False)
class LabelNode:
    items: Tuple[str, ...]

    def __init__(self, *items: str):
        object.__setattr__(self, "items", tuple(items))

    def merge(self, other: "LabelNode") -> "LabelNode":
        return LabelNode(*self.items, *other.items)

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


def _read_doc(filename: str, args, temp_dir) -> List[str]:
    if args.prep:
        assert temp_dir is not None
        doc = do_apply_preprocessors(args.prep, filename, temp_dir)
    else:
        with open(filename, "r") as inp:
            try:
                doc = inp.read()
            except Exception as e:
                sys.exit("Error in reading a file: %s\n%s" % (repr(filename), e))
    if args.char_by_char:
        return [c for c in doc]
    if args.line_by_line:
        return doc.split("\n")
    if args.tokenize:
        return text_split(doc, filename)
    return text_split_by_char_type(doc)


def _iter_documents(files: List[str], args):
    temp_dir_context = tempfile.TemporaryDirectory() if args.prep else nullcontext(None)
    with temp_dir_context as temp_dir:
        for filename in files:
            yield filename, _read_doc(filename, args, temp_dir)


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
                    labels[idx1] = labels[idx1].merge(labels[idx2])
                    indice_set_tobe_removed.add(idx2)

    indices_tobe_removed = list(indice_set_tobe_removed)
    indices_tobe_removed.sort(reverse=True)
    for i in indices_tobe_removed:
        del idocs[i]
        del labels[i]

    return idocs, labels


def select_neighbors(
    idocs: List[List[int]],
    labels: List[LabelNode],
    neighbors: int,
    progress: bool = False,
    distance_function: Callable[[List[int], List[int]], int] = distance_int_list,
) -> Tuple[List[List[int]], List[LabelNode]]:
    idocs = idocs[:]
    labels = labels[:]
    dds: List[Tuple[int, int]] = [(0, 0)]
    pbar = tqdm(desc="Identifying neighbors", total=len(idocs) - 1, leave=False) if progress else DummyProgressBar()
    for i in range(1, len(idocs)):
        d = distance_function(idocs[0], idocs[i])
        dds.append((d, i))
        pbar.update(1)
    pbar.close()
    dds.sort()
    dds = dds[: neighbors + 1]
    idocs = [idocs[i] for d, i in dds]
    labels = [labels[i] for d, i in dds]
    return idocs, labels


_distance_worker_idocs: Optional[List[List[int]]] = None
_distance_worker_function: Callable[[List[int], List[int]], int] = distance_int_list


def _init_distance_worker(
    idocs: List[List[int]], distance_function: Callable[[List[int], List[int]], int]
) -> None:
    global _distance_worker_idocs, _distance_worker_function
    _distance_worker_idocs = idocs
    _distance_worker_function = distance_function


def calc_dld(index_pair: Tuple[int, int]) -> Tuple[Tuple[int, int], int]:
    i, j = index_pair
    assert _distance_worker_idocs is not None
    return (i, j), _distance_worker_function(_distance_worker_idocs[i], _distance_worker_idocs[j])


def calc_dendrogram(idocs, progress=False, workers=None, distance_function=distance_int_list):
    import scipy.spatial.distance as distance
    from scipy.cluster.hierarchy import linkage

    if workers is None:
        workers = 1

    len_docs = len(idocs)
    jobs = ((i, j) for i in range(len_docs) for j in range(len_docs) if i < j)
    total_jobs = len_docs * (len_docs - 1) // 2
    pbar = tqdm(desc="Building dendrogram", total=total_jobs, leave=False) if progress else DummyProgressBar()
    dld_tbl = dict()
    try:
        with Pool(workers, initializer=_init_distance_worker, initargs=(idocs, distance_function)) as pool:
            for ij, v in pool.imap_unordered(calc_dld, jobs):
                dld_tbl[ij] = v
                pbar.update(1)
    except KeyboardInterrupt:
        print("\nWarning: Distance calculation interrupted.", file=sys.stderr)
        raise
    finally:
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

    parser.add_argument(
        '--no-numba', action='store_true',
        help='Use the pure-Python distance implementation instead of Numba.'
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


def _run_dendrogram_mode(
    docs: List[List[str]],
    labels: List[LabelNode],
    args,
    format_leaf_node: Callable[[LabelNode], str],
    tree_picture_table,
    distance_function: Callable[[List[int], List[int]], int],
) -> None:
    idocs, _word_to_index = convert_to_int_docs(docs)

    if args.neighbor_list is not None and args.neighbor_list != -1:
        label_strs = [label.format() for label in labels]
        do_listing_in_order_of_increasing_distance(
            label_strs,
            idocs,
            neighbors=args.neighbor_list,
            separator=args.field_separator or LABEL_HEADER,
            progress=args.progress,
            distance_function=distance_function,
        )
        return

    idocs, labels = merge_identical_idocs(idocs, labels)

    if len(idocs) <= 1:
        if args.pyplot:
            print("All documents are equivalent to each other.")
        else:
            root_node = labels[0]
            print_tree(root_node, extract_child_nodes, format_leaf_node, tree_picture_table=tree_picture_table)
        return

    if args.neighbors is not None and args.neighbors > 0 and len(idocs) > args.neighbors + 1:
        idocs, labels = select_neighbors(
            idocs, labels, args.neighbors, progress=args.progress, distance_function=distance_function
        )

    result = calc_dendrogram(
        idocs, progress=args.progress, workers=args.workers, distance_function=distance_function
    )
    if args.pyplot:
        label_strs = [label.format() for label in labels]
        pyplot_dendrogram(result, label_strs, font=args.pyplot_font)
    else:
        print_dendrogram(
            result, labels, format_leaf_node, max_depth=args.max_depth, tree_picture_table=tree_picture_table
        )


def _run_file_modes(
    files: List[str],
    args,
    format_leaf_node: Callable[[LabelNode], str],
    tree_picture_table,
    distance_function: Callable[[List[int], List[int]], int],
) -> None:
    if args.show_words:
        for _filename, words in _iter_documents(files, args):
            for word in words:
                print(word)
        return

    labels: List[LabelNode] = []
    docs: List[List[str]] = []
    for filename, doc in _iter_documents(files, args):
        labels.append(LabelNode(filename))
        docs.append(doc)

    if args.diff:
        if len(docs) != 2:
            sys.exit("Error: Option -d requires exactly two files.")
        do_diff(docs[0], docs[1], sep='\n' if args.line_by_line else '')
        return

    _run_dendrogram_mode(docs, labels, args, format_leaf_node, tree_picture_table, distance_function)


def main():
    parser = gen_parser()
    args = parser.parse_args()
    if not args.files:
        parser.print_help()
        return

    distance_function = distance_int_list_python if args.no_numba else distance_int_list
    if args.pyplot and args.max_depth is not None:
        sys.exit("Error: Options --pyplot and --max-depth are mutually exclusive.")
    if not args.pyplot and args.pyplot_font:
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

    files = args.files if (args.diff or args.no_uniq_files) else uniq(args.files)
    _run_file_modes(files, args, format_leaf_node, tree_picture_table, distance_function)
