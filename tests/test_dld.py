import unittest

from dendro_text.dld import distance_int_list, edit_sequence_int_list


class TestDistanceIntList(unittest.TestCase):
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


class TestEditSequenceIntList(unittest.TestCase):
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
