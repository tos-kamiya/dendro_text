# distutils: language = c++

from libcpp.vector cimport vector

# ref: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python


def distance_int(os1, os2):
    cdef vector[int] s1 = os1
    cdef vector[int] s2 = os2

    if len(s1) < len(s2):
        tmp = s1; s1 = s2; s2 = tmp
    assert len(s1) >= len(s2)

    if len(s2) == 0:
        return len(s1)

    previous_row = [i for i in range(len(s2) + 1)]
    cdef int i, c1, j, c2
    for i in range(len(s1)):
        c1 = s1[i]
        current_row = [i + 1]
        for j in range(len(s2)):
            c2 = s2[j]
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

