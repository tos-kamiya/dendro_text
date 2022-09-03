from typing import List as PList
from enum import IntFlag

# ref: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
# distance_int_list was copied from the above page and refactored somehow.

try:

    from numba import njit
    from numba.typed import List as TList


    @njit(nogil=True)
    def distance_int_list_i(s1, s2):
        if len(s1) < len(s2):
            tmp = s1
            s1 = s2
            s2 = tmp
        assert len(s1) >= len(s2)

        if len(s2) == 0:
            return len(s1)

        current_row = TList()
        current_row.extend(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            previous_row = current_row
            current_row = TList()
            current_row.append(i + 1)
            [current_row.append(0) for _ in s2]
            for j, c2 in enumerate(s2):
                d_ins = previous_row[j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
                d_del = current_row[j] + 1  # than s2
                d_sub = previous_row[j] + (c1 != c2)
                current_row[j + 1] = min(d_ins, d_del, d_sub)

        return current_row[-1]


    def distance_int_list(s1: PList[int], s2: PList[int]) -> int:
        ns1 = TList()
        [ns1.append(i) for i in s1]
        ns2 = TList()
        [ns2.append(i) for i in s2]
        return distance_int_list_i(ns1, ns2)


except ImportError:

    def distance_int_list(s1: PList[int], s2: PList[int]) -> int:
        if len(s1) < len(s2):
            tmp = s1
            s1 = s2
            s2 = tmp
        assert len(s1) >= len(s2)

        if len(s2) == 0:
            return len(s1)

        current_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            previous_row = current_row
            current_row = [i + 1] + [0] * len(s2)
            for j, c2 in enumerate(s2):
                d_ins = previous_row[j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
                d_del = current_row[j] + 1  # than s2
                d_sub = previous_row[j] + (c1 != c2)
                current_row[j + 1] = min(d_ins, d_del, d_sub)

        return current_row[-1]


class EditOp(IntFlag):
    SUB = 0
    DEL = 1
    INS = 2
    NO_EDIT = 3


def edit_sequence_to_str(edit_seq: PList[int]) -> str:
    r = []
    for eop in edit_seq:
        if eop == EditOp.SUB:
            r.append('m')
        elif eop == EditOp.DEL:
            r.append('d')
        elif eop == EditOp.INS:
            r.append('i')
        else:
            assert eop == EditOp.NO_EDIT
            r.append('-')

    return ''.join(r)


def trans_edit_sequence(edit_seq: PList[int]) -> PList[int]:
    r = []
    for eop in edit_seq:
        if eop == EditOp.DEL:
            eop = EditOp.INS
        elif eop == EditOp.INS:
            eop = EditOp.DEL
        r.append(eop)

    r = [int(eop) for eop in r]
    return r


def edit_sequence_int_list(s1: PList[int], s2: PList[int]) -> PList[int]:
    s1_s2_swapped = False
    if len(s1) < len(s2):
        tmp = s1
        s1 = s2
        s2 = tmp
        s1_s2_swapped = True
    assert len(s1) >= len(s2)

    rows = []
    current_row = list(range(len(s2) + 1))
    rows.append(current_row)
    for i, c1 in enumerate(s1):
        previous_row = current_row
        current_row = [i + 1] + [0] * len(s2)
        for j, c2 in enumerate(s2):
            d_ins = previous_row[j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
            d_del = current_row[j] + 1  # than s2
            d_sub = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(d_ins, d_del, d_sub)
        rows.append(current_row)

    edit_seq_r = []
    i, j = len(s1), len(s2)
    while i > 0 and j > 0:
        d_del = rows[i - 1][j]
        d_ins = rows[i][j - 1]
        d_sub = rows[i - 1][j - 1]
        d_min = min(d_del, d_ins, d_sub)
        if d_min == d_sub:
            edit_seq_r.append(EditOp.NO_EDIT if s1[i - 1] == s2[j - 1] else EditOp.SUB)
            i -= 1
            j -= 1
        elif d_min == d_del:
            edit_seq_r.append(EditOp.DEL)
            i -= 1
        else:
            assert d_min == d_ins
            edit_seq_r.append(EditOp.INS)
            j -= 1
    if i == 0:
        edit_seq_r.extend([EditOp.INS] * j)
    if j == 0:
        edit_seq_r.extend([EditOp.DEL] * i)
    edit_seq = [int(eop) for eop in reversed(edit_seq_r)]

    if s1_s2_swapped:
        edit_seq = trans_edit_sequence(edit_seq)

    return edit_seq
