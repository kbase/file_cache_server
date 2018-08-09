"""
Simple integration tests on the API itself.

We make actual ajax requests to the running docker container.
"""

import os
import unittest
import requests
from uuid import uuid4
import functools
from minio.error import NoSuchKey

import caching_service.minio as minio

url = 'http://web:5000/v1'
auth = os.environ['KBASE_AUTH_TOKEN']


@functools.lru_cache()
def get_cache_id(cache_params=None):
    if not cache_params:
        cache_params = '{"xyz":123}'
    resp = requests.post(
        url + '/cache_id',
        headers={'Authorization': auth, 'Content-Type': 'application/json'},
        data=cache_params
    )
    json = resp.json()
    cache_id = json['cache_id']
    return cache_id


@functools.lru_cache()
def upload_cache(cache_params=None, content=None):
    """Upload a cache file for repeatedly testing downloads/deletes/etc."""
    cache_id = get_cache_id(cache_params)
    if not content:
        content = b'{"hallo": "welt"}'
    requests.post(
        url + '/cache/' + cache_id,
        headers={'Authorization': auth},
        files={'file': ('test.json', content)}
    )
    return (cache_id, content)


class TestApiV1(unittest.TestCase):

    def test_root(self):
        """Test get paths."""
        resp = requests.get(url)
        json = resp.json()
        # Don't particularly feel the need to test the content of this
        self.assertTrue(json['routes'])

    def test_missing_auth(self):
        """Test the error response for all endpoints that require the Authentication header."""
        endpoints = [
            {'method': 'POST', 'url': url + '/cache_id'},
            {'method': 'GET', 'url': url + '/cache/example'},
            {'method': 'POST', 'url': url + '/cache/example'},
            {'method': 'DELETE', 'url': url + '/cache/example'}
        ]
        for req_data in endpoints:
            resp = requests.post(req_data['url'], headers={})
            json = resp.json()
            self.assertEqual(resp.status_code, 400, 'Status code is 400')
            self.assertEqual(json['status'], 'error', 'Status is set to "error"')
            self.assertTrue('Missing header' in json['error'], 'Error message is set')

    def test_invalid_auth(self):
        """Test the error response for all endpoints that require valid auth."""
        endpoints = [
            {'method': 'POST', 'url': url + '/cache_id'},
            {'method': 'GET', 'url': url + '/cache/example'},
            {'method': 'POST', 'url': url + '/cache/example'},
            {'method': 'DELETE', 'url': url + '/cache/example'}
        ]
        for req_data in endpoints:
            resp = requests.post(req_data['url'], headers={'Authorization': auth + 'x'})
            json = resp.json()
            self.assertEqual(resp.status_code, 403, 'Status code is 403')
            self.assertEqual(json['status'], 'error', 'Status is set to "error"')
            self.assertTrue('Invalid token' in json['error'], 'Error message is set')

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
        self.assertEqual(json['status'], 'ok', 'Status is "generated"')
        self.assertEqual(len(json['cache_id']), 64, 'Creates 64-byte cache ID')

    def test_make_cache_id_malformed_json(self):
        """
        Test a call to make a cache ID with invalid JSON formatting.

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': auth, 'Content-Type': 'application/json'},
            data='{{{{(((('
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json['status'], 'error', 'Status is "error"')
        self.assertTrue('JSON parsing error' in json['error'], 'Error message is set')

    def test_make_cache_id_unauthorized(self):
        """
        Test a call to create a new cache ID with an invalid auth token.

        POST /cache_id
        """
        resp = requests.post(
            url + '/cache_id',
            headers={'Authorization': auth + 'x', 'Content-Type': 'application/json'},
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

    def test_download_cache_file_valid(self):
        """
        Test a call to download an existing cache file successfully.

        GET /cache/<cache_id>
        """
        (cache_id, content) = upload_cache()
        resp = requests.get(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, content)

    def test_download_cache_file_unauthorized_cache(self):
        """
        Test a call to download a cache file that was made by a different token ID

        GET /cache/<cache_id>
        """
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, 'test_user')
        resp = requests.get(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 403, 'Status code is 403')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('You do not have access' in json['error'])

    def test_download_cache_file_missing_cache(self):
        """
        Test a call to download a cache file that does not exist

        GET /cache/<cache_id>
        """
        cache_id = str(uuid4())
        resp = requests.get(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json['status'], 'error')
        self.assertTrue('not found' in json['error'])

    def test_upload_cache_file_valid(self):
        """
        Test a call to upload a cache file successfully.

        POST /cache/<cache_id>
        """
        cache_id = get_cache_id()
        content = b'{"hallo": "welt"}'
        resp = requests.post(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth},
            files={'file': ('test.json', content)}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json['status'], 'ok')

    def test_upload_cache_file_unauthorized_cache(self):
        """
        Test a call to upload a cache file successfully.

        POST /cache/<cache_id>
        """
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, 'test_user')
        resp = requests.post(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth},
            files={'file': ('test.json', b'{"x": 1}')}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 403, 'Status code is 403')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('You do not have access' in json['error'])

    def test_upload_cache_file_missing_cache(self):
        """
        Test a call to upload a cache file successfully.

        POST /cache/<cache_id>
        """
        cache_id = str(uuid4())
        resp = requests.post(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth},
            files={'file': ('test.json', b'{"x": 1}')}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 404, 'Status code is 404')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('not found' in json['error'])

    def test_upload_cache_file_missing_file(self):
        """
        Test a call to upload a cache file successfully.

        POST /cache/<cache_id>
        """
        cache_id = get_cache_id()
        resp = requests.post(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth},
            files={'filexx': ('test.json', b'{"x": 1}')}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 400, 'Status code is 400')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('missing' in json['error'])

    def test_delete_valid(self):
        """
        Test a valid deletion of a cache entry.

        DELETE /cache/<cache_id>
        """
        cache_id = get_cache_id()
        resp = requests.delete(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 200, 'Status code is 200')
        self.assertEqual(json['status'], 'ok', 'Status is "deleted"')
        # Test that the cache is inaccessible
        with self.assertRaises(NoSuchKey):
            minio.get_metadata(cache_id)

    def test_delete_unauthorized_cache(self):
        """
        Test a deletion of a cache entry with a cache created by a different token ID.

        DELETE /cache/<cache_id>
        """
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, 'test_user')
        resp = requests.delete(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 403, 'Status code is 403')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('You do not have access' in json['error'])

    def test_delete_missing_cache(self):
        """
        Test a deletion of a nonexistent cache entry

        DELETE /cache/<cache_id>
        """
        cache_id = str(uuid4())
        resp = requests.delete(
            url + '/cache/' + cache_id,
            headers={'Authorization': auth}
        )
        json = resp.json()
        self.assertEqual(resp.status_code, 404, 'Status code is 404')
        self.assertEqual(json['status'], 'error', 'Status is set to "error"')
        self.assertTrue('not found' in json['error'])
