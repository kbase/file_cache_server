"""
A simple server stress tester.

This is for stress testing gunicorn, flask, leveldb, and minio with a lot of parallel requests or
with very large files.
"""

import unittest
import grequests
import requests
import os
import time
from uuid import uuid4


def exception_handler(request, exception):
    """Any request from grequests has failed."""
    print('Request failed')
    print(request)
    raise exception


class TestServerStress(unittest.TestCase):

    def setUp(self):
        self.base_url = 'http://web:5000'

    def test_large_files(self):
        """Test Minio by uploading a several very large files at once."""
        one_gb = 1024 * 1024 * 1024
        with open('large_file', 'wb') as fout:
            fout.write(os.urandom(one_gb))
        start = time.time()
        # Measure the time it takes to upload and delete a single 1gb file
        with open('large_file', 'rb') as f:
            files = {'file': f}
            response = requests.post(
                self.base_url + '/v1/cache_id',
                headers={'Authorization': 'non_admin_token', 'Content-Type': 'application/json'},
                data='{"xyz": 123}'
            )
            cache_id = response.json()['cache_id']
            requests.post(
                self.base_url + '/v1/cache/' + cache_id,
                files=files,
                headers={'Authorization': 'non_admin_token'}
            )
        requests.delete(
            self.base_url + '/v1/cache/' + cache_id,
            headers={'Authorization': 'non_admin_token'}
        )
        time_diff = time.time() - start
        print('Total time for one file: ' + str(time_diff))
        # Measure the time it takes to upload many 1gb files at once
        start = time.time()
        reqs = []  # type: list
        cache_ids = []  # type: list
        concurrent_files = 10
        # Generate cache ids for each file
        for idx in range(concurrent_files):
            req = grequests.post(
                self.base_url + '/v1/cache_id',
                headers={'Authorization': 'non_admin_token', 'Content-Type': 'application/json'},
                data='{"xyz":"' + str(uuid4()) + '"}'
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        cache_ids = list(map(lambda r: r.json()['cache_id'], responses))
        reqs = []
        # Upload many 1gb files at once
        with open('large_file', 'rb') as f:
            files = {'file': f}
            for cache_id in cache_ids:
                req = grequests.post(
                    self.base_url + '/v1/cache/' + cache_id,
                    files=files,
                    headers={'Authorization': 'non_admin_token'}
                )
                reqs.append(req)
            responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        os.remove('large_file')
        # Finally, delete everything that we uploaded
        reqs = []
        for cache_id in cache_ids:
            req = grequests.delete(
                self.base_url + '/v1/cache/' + cache_id,
                headers={'Authorization': 'non_admin_token'}
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        time_diff = time.time() - start
        print('Total time for ' + str(concurrent_files) + ' files: ' + str(time_diff))

    def test_many_connections(self):
        """Test flask, gunicorn, and leveldb by making a lot of requests at once."""
        # Create
        reqs = []
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'non_admin_token'
        }
        # Create a small test file for uploading
        with open('test.json', 'w+') as fwrite:
            fwrite.write('{}')
        # Generate a lot of unique cache IDs in parallel
        for i in range(1000):
            req = grequests.post(
                self.base_url + '/v1/cache_id',
                data='{"xyz":"' + str(uuid4()) + '"}',
                headers=headers
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        # Get all the plain-string cache ids from all the responses
        cache_ids = list(map(lambda r: r.json()['cache_id'], responses))
        # Upload small cache files
        reqs = []
        file_obj = open('test.json', 'rb')
        for cid in cache_ids:
            req = grequests.post(
                self.base_url + '/v1/cache/' + cid,
                files={'file': file_obj},
                headers={'Authorization': 'non_admin_token'}
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        file_obj.close()
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        # Fetch all cache files
        reqs = []
        for cid in cache_ids:
            req = grequests.get(
                self.base_url + '/v1/cache/' + cid,
                headers=headers
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        # Delete all cache files
        reqs = []
        for cid in cache_ids:
            req = grequests.delete(
                self.base_url + '/v1/cache/' + cid,
                headers=headers
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        # Delete the test file
        os.remove('test.json')
