"""
Simple integration tests on the API itself using `requests`.
"""

import os
import unittest
import requests

url = 'http://web:5000/v1'
auth = os.environ['KBASE_AUTH_TOKEN']


class TestApiV1(unittest.TestCase):

    def test_root(self):
        """Test get paths."""
        resp = requests.get(url)
        json = resp.json()
        # Don't particularly feel the need to test the content of this
        self.assertTrue(json['routes'])

    def test_make_cache_id_valid(self):
        """
        Test a valid call to create a new cache ID.

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': auth, 'Content-Type': 'application/json'},
            data='{"xyz": 123}'
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json['status'], 'generated', 'Status is "generated"')
        self.assertEqual(len(json['cache_id']), 64, 'Creates 64-byte cache ID')

    def test_make_cache_id_unauthorized(self):
        """
        Test a call to create a new cache ID with an invalid auth token.

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': 'invalid', 'Content-Type': 'application/json'},
            data='{"xyz": 123}'
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 403, 'Status code is 403')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('Invalid token' in json['error'], 'Gives error message')

    def test_make_cache_id_wrong_content_type(self):
        """
        Test a call to create a new cache ID with the wrong content-type.

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': auth, 'Content-Type': 'multipart/form-data'},
            data='{"xyz": 123}'
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 400, 'Status code is 400')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('Invalid Content-Type' in json['error'])

    def test_make_cache_id_missing_content_type(self):
        """
        Test a call to create a new cache ID with missing content-type.

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': auth},
            data='{"xyz": 123}'
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 400, 'Status code is 400')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('Invalid Content-Type' in json['error'])

    def test_make_cache_id_missing_authorization(self):
        """
        Test a call to create a new cache ID with missing authorization

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Content-Type': 'application/json'},
            data='{"xyz": 123}'
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 400, 'Status code is 400')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('Missing header' in json['error'])

    def test_make_cache_id_missing_json(self):
        """
        Test a call to create a new cache ID with missing authorization

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': auth, 'Content-Type': 'application/json'}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 400, 'Status code is 400')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('JSON parsing error' in json['error'])
