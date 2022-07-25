import unittest

from dendro_text.dld import distance_int


class TestPrintTree(unittest.TestCase):
    def test_small_lists(self):
        list1 = [1] * 3 + [2] * 9 + [3] * 2
        list2 = [1] * 3 + [2] * 8 + [3] * 2
        list3 = [1] * 3 + [2] * 6 + [3] * 2

        d = distance_int(list1, list2)
        self.assertEqual(d, 1)

        d = distance_int(list1, list3)
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

        d = distance_int(list1, list2)
        self.assertEqual(d, 800)


if __name__ == "__main__":
    unittest.main()
