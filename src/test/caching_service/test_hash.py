import time
import unittest

from src.caching_service.hash import bhash


class TestHash(unittest.TestCase):

    def test_basic(self):
        h1 = bhash('1234567890')
        expected = '68d6ef20266276f163541b9db63db73bc5e6351755b741dbf59c3dcdf6678951a65e0844e238d6d25ae7e4293fcf29f913d02cd68ba1925615865d1aaa50fe8e'  # noqa
        self.assertEqual(h1, expected)
        h2 = bhash('1234567890')
        self.assertEqual(h1, h2)

    def test_empty(self):
        with self.assertRaises(TypeError):
            bhash('')

    def test_wrong_type(self):
        with self.assertRaises(TypeError):
            bhash(123)

    def test_uniform_len(self):
        """All hashes are the same length regardless of input value."""
        h1 = bhash('xyz')
        h2 = bhash('xyzxyzxyzxyzxyz')
        self.assertEqual(len(h1), len(h2))

    def test_very_long(self):
        start = time.time()
        h = bhash('abcdefghij' * 1000)  # 10kb string
        diff = time.time() - start
        expected = 'acbe8b86215c2d5a6bdcc9ccd98ccac597a9b43021dff12e3f805edf68cf2f379a53602b42fe79a6a5da1247a9ff979c90ff56f15b442c2dca5145ce5676a72b'  # noqa
        self.assertEqual(h, expected)
        # blake2b hashes at around 1mb per second -- 10kb should be well under 1s
        self.assertTrue(diff < 1)
