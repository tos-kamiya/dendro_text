import os
import subprocess
import sys
import unittest

from dendro_text.dld import EditOp, distance_int_list, edit_sequence_int_list


class TestDistanceIntList(unittest.TestCase):
    def test_empty_lists(self):
        self.assertEqual(distance_int_list([], []), 0)
        self.assertEqual(distance_int_list([1, 2], []), 2)
        self.assertEqual(distance_int_list([], [1, 2]), 2)

    def test_symmetric(self):
        list1 = [1, 2, 3, 2]
        list2 = [1, 4, 2]
        self.assertEqual(distance_int_list(list1, list2), distance_int_list(list2, list1))

    def test_small_lists(self):
        list1 = [1] * 3 + [2] * 9 + [3] * 2
        list2 = [1] * 3 + [2] * 8 + [3] * 2
        list3 = [1] * 3 + [2] * 6 + [3] * 2

        d = distance_int_list(list1, list2)
        self.assertEqual(d, 1)

        d = distance_int_list(list1, list3)
        self.assertEqual(d, 3)

    def test_long_lists(self):
        def swap(i, j, lst):
            tmp = lst[i]
            lst[i] = lst[j]
            lst[j] = tmp

        list1 = [i for i in range(4000)]
        list2 = [i for i in range(4000)]

        for i in range(1, 4000, 10):
            swap(i, i + 5, list2)

        d = distance_int_list(list1, list2)
        self.assertEqual(d, 800)

    def test_numba_backend_if_available(self):
        import dendro_text.dld as dld

        if not hasattr(dld, "distance_int_list_i"):
            self.skipTest("Numba is not installed")
        self.assertEqual(dld.distance_int_list([1, 2, 3], [1, 3]), 1)


class TestPurePythonFallback(unittest.TestCase):
    def test_fallback_when_numba_import_fails(self):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script = """
import builtins
import sys

real_import = builtins.__import__
def blocked_numba(name, *args, **kwargs):
    if name == 'numba' or name.startswith('numba.'):
        raise ImportError('forced fallback test')
    return real_import(name, *args, **kwargs)

builtins.__import__ = blocked_numba
from dendro_text.dld import distance_int_list
assert distance_int_list([1, 2, 3], [1, 3]) == 1
"""
        env = os.environ.copy()
        env["PYTHONPATH"] = project_dir
        completed = subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


class TestEditSequenceIntList(unittest.TestCase):
    def test_edit_sequence_cost_matches_distance(self):
        examples = [
            ([1, 2, 3], [1, 3]),
            ([1, 2], [2, 1, 2]),
            ([], [1, 2]),
            ([4, 4, 2, 2, 3], [1, 2, 2, 3]),
        ]
        for list1, list2 in examples:
            with self.subTest(list1=list1, list2=list2):
                edit_sequence = edit_sequence_int_list(list1, list2)
                edit_count = sum(op != EditOp.NO_EDIT for op in edit_sequence)
                self.assertEqual(edit_count, distance_int_list(list1, list2))

    def test_small_lists(self):
        list1 = [1] * 1 + [2] * 3 + [3] * 1
        list2 = [1] * 1 + [2] * 2 + [3] * 1

        s = edit_sequence_int_list(list1, list2)
        self.assertSequenceEqual(s, [3, 3, 3, 1, 3])
        s = edit_sequence_int_list(list2, list1)
        self.assertSequenceEqual(s, [3, 3, 3, 2, 3])

        list1m1 = list1[:]
        list1m1[0] = 4

        s = edit_sequence_int_list(list1m1, list2)
        self.assertSequenceEqual(s, [0, 3, 3, 1, 3])
        s = edit_sequence_int_list(list2, list1m1)
        self.assertSequenceEqual(s, [0, 3, 3, 2, 3])

        list1m2 = list1[:]
        list1m2[-1] = 4

        s = edit_sequence_int_list(list1m2, list2)
        self.assertSequenceEqual(s, [3, 3, 3, 1, 0])
        s = edit_sequence_int_list(list2, list1m2)
        self.assertSequenceEqual(s, [3, 3, 3, 2, 0])

        list1m3 = [4, 4, 2, 2, 3]

        s = edit_sequence_int_list(list1m3, list2)
        self.assertSequenceEqual(s, [1, 0, 3, 3, 3])
        s = edit_sequence_int_list(list2, list1m3)
        self.assertSequenceEqual(s, [2, 0, 3, 3, 3])


if __name__ == "__main__":
    unittest.main()
