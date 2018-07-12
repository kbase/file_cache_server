"""
A simple server stress tester.

This is for stress testing gunicorn, flask, leveldb, and minio with a lot of parallel requests or
with very large files.
"""

import json
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
            requests.post(
                self.base_url + '/v1/cache/large_file',
                files=files,
                headers={'Authorization': 'xyz'}
            )
        requests.delete(
            self.base_url + '/v1/cache/large_file',
            headers={'Authorization': 'xyz'}
        )
        time_diff = time.time() - start
        print('Total time for one file: ' + str(time_diff))
        # Measure the time it takes to upload four 1gb files at once
        start = time.time()
        reqs = []
        concurrent_files = 10
        with open('large_file', 'rb') as f:
            files = {'file': f}
            for idx in range(concurrent_files):
                req = grequests.post(
                    self.base_url + '/v1/cache/large_file' + str(idx),
                    files=files,
                    headers={'Authorization': 'xyz'}
                )
                reqs.append(req)
            responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        os.remove('large_file')
        reqs = []
        for idx in range(concurrent_files):
            req = grequests.delete(
                self.base_url + '/v1/cache/large_file' + str(idx),
                headers={'Authorization': 'xyz'}
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
            'Authorization': 'xyzxyz'
        }
        # Create a small test file for uploading
        with open('test.json', 'w+') as fwrite:
            fwrite.write('{}')
        # Generate a lot of unique cache IDs in parallel
        for i in range(1000):
            req = grequests.post(
                self.base_url + '/v1/cache_id',
                data=json.dumps({'xyz': str(uuid4())}),
                headers=headers,
                # timeout=1.0
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        # Get all the plain-string cache ids from all the responses
        cache_ids = list(map(lambda r: json.loads(r.content)['cache_id'], responses))
        # Upload small cache files
        reqs = []
        headers['Content-Type'] = 'multipart/form-data'
        open_files = []
        create_file_headers = {
            'Authorization': 'xyz'
        }
        file_obj = open('test.json', 'rb')
        for cid in cache_ids:
            open_files.append(file_obj)
            files = {'file': file_obj}
            req = grequests.post(
                self.base_url + '/v1/cache/' + cid,
                files=files,
                headers=create_file_headers,
                # timeout=5.0
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        file_obj.close()
        for f in open_files:
            f.close()
        for resp in responses:
            self.assertEqual(resp.status_code, 200)
        # Fetch all cache files
        reqs = []
        headers['Content-Type'] = 'application/json'
        for cid in cache_ids:
            req = grequests.get(
                self.base_url + '/v1/cache/' + cid,
                headers=headers,
                # timeout=5.0
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
                headers=headers,
                # timeout=5.0
            )
            reqs.append(req)
        responses = grequests.map(reqs, exception_handler=exception_handler)
        for resp in responses:
            if resp.status_code != 200:
                print('=' * 100)
                print(resp.content)
                print('=' * 100)
            self.assertEqual(resp.status_code, 200)
        print('-' * 100)
        print('Ideally, these tests should have completed in less than 30s')
        print('If not, try setting your number of gunicorn workers to (2 * $num_cores) + 1')
        # Delete the test file
        os.remove('test.json')
