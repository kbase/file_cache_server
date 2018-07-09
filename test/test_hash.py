import time
from caching_service.hash import bhash
import unittest


class TestHash(unittest.TestCase):

    def test_basic(self):
        h1 = bhash('1234567890')
        expected = '807f1ba73147c3a96c2d63b38dd5a5f514f66290a1436bb9821e9f2a72eff263'
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
        expected = '1d9bae0966881e51b78b268589f1da7053e397df36c8eba91a905340266019c1'
        self.assertEqual(h, expected)
        # blake2b hashes at around 1mb per second -- 10kb should be well under 1s
        self.assertTrue(diff < 1)
