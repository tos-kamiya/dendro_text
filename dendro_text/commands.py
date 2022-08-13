from typing import List, Tuple

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


DEL_BEGIN = "\x1b[41m"
DEL_END = "\x1b[0m"
INS_BEGIN = "\x1b[44m"
INS_END = "\x1b[0m"


def do_diff(ldoc: List[str], lidoc: List[int], rdoc: List[str], ridoc: List[int], sep: str = '') -> None:
    es = edit_sequence_int_list(lidoc, ridoc)
    li = ri = 0
    for eop in es:
        if eop == EditOp.NO_EDIT:
            sys.stdout.write(ldoc[li])
            li += 1
            ri += 1
        elif eop == EditOp.DEL:
            sys.stdout.write("%s%s%s" % (DEL_BEGIN, ldoc[li], DEL_END))
            li += 1
        elif eop == EditOp.INS:
            sys.stdout.write("%s%s%s" % (INS_BEGIN, rdoc[ri], INS_END))
            ri += 1
        else:
            assert eop == EditOp.SUB
            h, t, lw, rw = strip_common_head_and_tail(ldoc[li], rdoc[ri])
            sys.stdout.write("%s%s%s%s%s%s%s%s" % (h, DEL_BEGIN, lw, DEL_END, INS_BEGIN, rw, INS_END, t))
            li += 1
            ri += 1

        sys.stdout.write(sep)
