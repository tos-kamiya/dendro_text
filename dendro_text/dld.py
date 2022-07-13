from typing import List


# ref: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python


def distance_int(s1, s2):
    if len(s1) < len(s2):
        tmp = s1
        s1 = s2
        s2 = tmp
    assert len(s1) >= len(s2)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = (
                previous_row[j + 1] + 1
            )  # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1  # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def distance_list(lst1: List[str], lst2: List[str]) -> int:
    w2i = dict()

    def convert(lst: List[str]) -> List[int]:
        a1 = []
        for w in lst:
            i = w2i.get(w, None)
            if i is None:
                i = len(w2i) + 1
                w2i[w] = i
            a1.append(i)
        return a1

    a1 = convert(lst1)
    a2 = convert(lst2)
    return distance_int(a1, a2)
