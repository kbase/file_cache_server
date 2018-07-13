import caching_service.minio as minio
import unittest
import re
import shutil
import time
import io
from werkzeug.datastructures import FileStorage
from minio.error import NoSuchKey
from uuid import uuid4

import caching_service.exceptions as exceptions


class TestMinio(unittest.TestCase):

    def make_test_file_storage(self, cache_id, token_id):
        """
        Create a FileStorage object for use in minio.cache_upload.

        FileStorage docs: http://werkzeug.pocoo.org/docs/0.14/datastructures/#others
        """
        filename = 'test.json'
        minio.create_placeholder(cache_id, token_id)
        contents = io.BytesIO(b'contents')
        return FileStorage(
            filename=filename,
            stream=contents
        )

    def test_placeholder_creation(self):
        """Test the creation of a cache file placeholder."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        minio.authorize_access(cache_id, token_id)
        (save_path, tmp_dir) = minio.download_cache(cache_id, token_id)
        print(save_path, tmp_dir)
        self.assertRegex(save_path, re.compile('^.+\/placeholder'))
        with open(save_path, 'rb') as placeholder:
            contents = placeholder.read()
            self.assertEqual(contents, b'')
        shutil.rmtree(tmp_dir)
        metadata = minio.get_metadata(cache_id)
        self.assertTrue(int(metadata[minio.metadata_expiration_key]) > time.time())
        self.assertEqual(metadata[minio.metadata_filename_key], 'placeholder')
        self.assertEqual(metadata[minio.metadata_token_id_key], token_id)

    def test_cache_upload(self):
        """Test a valid file upload to a cache ID."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        file_storage = self.make_test_file_storage(cache_id, token_id)
        minio.upload_cache(cache_id, token_id, file_storage)
        file_storage.stream.close()
        metadata = minio.get_metadata(cache_id)
        self.assertTrue(int(metadata[minio.metadata_expiration_key]) > time.time(),
                        'Expiration is in the future')
        self.assertEqual(metadata[minio.metadata_filename_key], file_storage.filename,
                         'Correct filename is saved in the metadata')
        self.assertEqual(metadata[minio.metadata_token_id_key], token_id,
                         'Correct token ID is saved in the metadata')
        (save_path, tmp_dir) = minio.download_cache(cache_id, token_id)
        with open(save_path, 'rb') as saved_file:
            saved_contents = saved_file.read().decode('utf-8')
            self.assertEqual(saved_contents, 'contents', 'Correct file contents uploaded')

    def test_cache_delete(self):
        """Test a valid file deletion."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        minio.delete_cache(cache_id, token_id)
        with self.assertRaises(NoSuchKey):
            minio.download_cache(cache_id, token_id)

    def test_unauthorized_download(self):
        """Test a download to the wrong token ID."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        with self.assertRaises(exceptions.UnauthorizedCacheAccess):
            minio.download_cache(cache_id, token_id + 'x')

    def test_unauthorized_upload(self):
        """Test an upload to the wrong token ID."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        file_storage = self.make_test_file_storage(cache_id, token_id)
        minio.create_placeholder(cache_id, token_id)
        with self.assertRaises(exceptions.UnauthorizedCacheAccess):
            minio.upload_cache(cache_id, token_id + 'x', file_storage)
        file_storage.stream.close()

    def test_missing_cache_upload(self):
        """Test an upload to a missing cache ID."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        file_storage = self.make_test_file_storage(cache_id, token_id)
        minio.create_placeholder(cache_id, token_id)
        with self.assertRaises(NoSuchKey):
            minio.upload_cache(cache_id + 'x', token_id, file_storage)
        file_storage.stream.close()

    def test_missing_cache_download(self):
        """Test a download to a missing cache ID."""
        token_id = 'user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        with self.assertRaises(NoSuchKey):
            minio.download_cache(cache_id + 'x', token_id)
