from caching_service.hash import bhash
import unittest


class TestHash(unittest.TestCase):

    def test_basic(self):
        h = bhash('1234567890')
        expected = '807f1ba73147c3a96c2d63b38dd5a5f514f66290a1436bb9821e9f2a72eff26'
        self.assertEqual(h, expected)
