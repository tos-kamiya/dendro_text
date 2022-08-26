from sre_constants import IN
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

import os.path
import subprocess
import sys

from tqdm import tqdm

from .dld import distance_int_list
from .dld import edit_sequence_int_list, EditOp
from .ts import strip_common_head_and_tail


class DummyProgressBar:
    def __init__(self):
        pass

    def update(self, value):
        pass

    def close(self):
        pass


def pyplot_dendrogram(result, label_strs, font=None):
    from scipy.cluster.hierarchy import dendrogram
    import matplotlib.pyplot as plt

    if font:
        import matplotlib as mpl

        mpl.rcParams["font.family"] = font
    plt.figure()
    dendrogram(result, labels=label_strs, orientation="right")
    # dendrogram(result, labels=[i for i in range(len_docs)], orientation='right')  # for debug
    plt.show()


def do_listing_pyplot_font_names():
    import matplotlib.font_manager as fm

    font_names = list(set(f.name for f in fm.fontManager.ttflist))
    font_names.sort()
    print("\n".join(font_names))


def do_apply_preprocessors(preprocessors: List[str], target_file: str, temp_dir: str) -> str:
    if len(preprocessors) == 1:
        try:
            cmd = " ".join([preprocessors[0], target_file])
            r = subprocess.check_output(cmd, shell=True)
            doc = r.decode("utf-8")
            return doc
        except Exception as e:
            sys.exit("Error in preprocessing a file: %s" % repr(target_file))
            raise e

    base_name = os.path.basename(target_file)
    tmp_file = os.path.join(temp_dir, base_name)
    with open(target_file, "rb") as inp:
        tmp_file_content: bytes = inp.read()
    for prep in preprocessors:
        with open(tmp_file, "wb") as outp:
            outp.write(tmp_file_content)
        try:
            cmd = " ".join([prep, tmp_file])
            tmp_file_content = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            sys.exit("Error in preprocessing a file: %s" % repr(target_file))
            raise e
    doc = tmp_file_content.decode("utf-8")
    return doc


def do_listing_in_order_of_increasing_distance(
    labels: List[str], idocs: List[List[int]], neighbors: int = -1, separator: str = "\t", progress: bool = False
) -> None:
    dds: List[Tuple[int, int]] = [(0, 0)]
    pbar = tqdm(desc="Identifying neighbors", total=len(idocs) - 1, leave=False) if progress else DummyProgressBar()
    for i in range(1, len(idocs)):
        d = distance_int_list(idocs[0], idocs[i])
        dds.append((d, i))
        pbar.update(1)
    pbar.close()
    dds.sort()

    if neighbors > 0:
        dds = dds[: neighbors + 1]
    for dist, doci in dds:
        print("%d%s%s" % (dist, separator, labels[doci]))


def convert_to_int_docs(docs: List[List[str]]) -> Tuple[List[List[int]], Dict[str, int]]:
    word_set = set()
    for doc in docs:
        word_set.update(doc)
    words = list(word_set)
    words.sort()
    word_to_index = dict((w, i + 1) for i, w in enumerate(words))
    idocs = [[word_to_index[w] for w in doc] for doc in docs]
    return idocs, word_to_index


DEL_BEGIN = "\x1b[101m"
DEL_END = "\x1b[0m"
INS_BEGIN = "\x1b[104m"
INS_END = "\x1b[0m"

WriteFunctionUnusedReturnValue = TypeVar("WriteFunctionUnusedReturnValue")


def do_diff(
    ldoc: List[str],
    rdoc: List[str],
    write: Optional[Callable[[str], WriteFunctionUnusedReturnValue]] = None,
    lbegend: Optional[Tuple[str, str]] = None,
    rbegend: Optional[Tuple[str, str]] = None,
    sep: str = '',
) -> None:
    if write is None:
        write = sys.stdout.write
    assert write is not None
    (lbeg, lend) = (DEL_BEGIN, DEL_END) if lbegend is None else lbegend
    (rbeg, rend) = (INS_BEGIN, INS_END) if rbegend is None else rbegend

    docs = [ldoc, rdoc]
    idocs, _word_to_index = convert_to_int_docs(docs)
    lidoc, ridoc = idocs[0], idocs[1]

    es = edit_sequence_int_list(lidoc, ridoc)
    li = ri = 0
    i = 0
    len_es = len(es)
    while i < len_es:
        if es[i] == EditOp.NO_EDIT:
            ws = []
            while i < len_es and es[i] == EditOp.NO_EDIT:
                ws.append(ldoc[li])
                li += 1
                ri += 1
                i += 1
            write("%s%s" % (sep.join(ws), sep))
        else:
            lws = []
            rws = []
            while i < len_es and es[i] != EditOp.NO_EDIT:
                esi = es[i]
                if esi == EditOp.DEL:
                    lws.append(ldoc[li])
                    li += 1
                elif esi == EditOp.INS:
                    rws.append(rdoc[ri])
                    ri += 1
                else:
                    assert esi == EditOp.SUB
                    lws.append(ldoc[li])
                    li += 1
                    rws.append(rdoc[ri])
                    ri += 1
                i += 1

            if not rws:
                assert lws
                write("%s%s%s%s" % (lbeg, sep.join(lws), lend, sep))
            elif not lws:
                write("%s%s%s%s" % (rbeg, sep.join(rws), rend, sep))
            else:
                if '\n' not in sep:
                    h, t, lw, rw = strip_common_head_and_tail(''.join(lws), ''.join(rws))
                    write("%s%s%s%s%s%s%s%s" % (h, lbeg, lw, lend, rbeg, rw, rend, t))
                else:
                    lsep = lend + sep + lbeg
                    rsep = rend + sep + rbeg
                    write("%s%s%s%s%s%s%s%s" % (lbeg, lsep.join(lws), lend, sep, rbeg, rsep.join(rws), rend, sep))

