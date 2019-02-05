import unittest

from caching_service.generate_cache_id import generate_cache_id


class TestMinio(unittest.TestCase):

    def test_valid(self):
        """Test a valid cache ID generation."""
        token_id = 'url:user:name'
        json_data = {'xyz': 123}
        cid = generate_cache_id(token_id, json_data)
        self.assertEqual(len(cid), 128, 'Creates 128-byte hash')

    def test_empty_json(self):
        """Pass an empty json data hash and check for the error."""
        token_id = 'url:user:name'
        json_data = {}  # type: dict
        with self.assertRaises(TypeError):
            generate_cache_id(token_id, json_data)

    def test_empty_token_id(self):
        """Pass an empty json data hash and check for the error."""
        token_id = ''
        json_data = {'xyz': 123}
        with self.assertRaises(TypeError):
            generate_cache_id(token_id, json_data)

    def test_invalid_json_data_type(self):
        """Pass a non-jsonifiable type and check for error."""
        token_id = 'url:user:name'
        json_data = unittest
        with self.assertRaises(TypeError):
            generate_cache_id(token_id, json_data)

    def test_invalid_token_id_type(self):
        token_id = unittest
        json_data = {'xyz': 123}
        with self.assertRaises(TypeError):
            generate_cache_id(token_id, json_data)

    def test_unique_cache_ids(self):
        """
        Even if you use the exact same json_data but different token IDs, the hash should be
        different.
        """
        token_id1 = 'user1:name'
        token_id2 = 'user2:name'
        json_data = {'xyz': 123}
        cid1 = generate_cache_id(token_id1, json_data)
        cid2 = generate_cache_id(token_id2, json_data)
        self.assertNotEqual(cid1, cid2, 'Different token IDs yield different hashes.')

    def test_repeated_cache_ids(self):
        """
        If you generate a cache ID twice using the same token_id and json_data, then you should get
        the same hash both times.
        """
        token_id = 'url:user:name'
        json_data = {'xyz': 123}
        cid1 = generate_cache_id(token_id, json_data)
        cid2 = generate_cache_id(token_id, json_data)
        self.assertEqual(cid1, cid2,
                         'Two generations with the same token/json should be the same hash.')
