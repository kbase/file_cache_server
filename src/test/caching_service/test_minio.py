import unittest
import shutil
import time
import os
import io
from werkzeug.datastructures import FileStorage
from uuid import uuid4
import tempfile

import src.caching_service.minio as minio
import src.caching_service.exceptions as exceptions


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
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        minio.authorize_access(cache_id, token_id)
        tmp_dir = tempfile.mkdtemp()
        with self.assertRaises(exceptions.MissingCache):
            minio.download_cache(cache_id, token_id, tmp_dir)
        save_path = os.path.join(tmp_dir, 'x')
        minio.minio_client.fget_object(minio.Config.minio_bucket_name, cache_id, save_path)
        with open(save_path, 'rb') as fd:
            contents = fd.read()
            self.assertEqual(contents, b'')
        shutil.rmtree(tmp_dir)
        metadata = minio.get_metadata(cache_id)
        self.assertTrue(int(metadata['expiration']) > time.time())
        self.assertEqual(metadata['filename'], 'placeholder')
        self.assertEqual(metadata['token_id'], token_id)

    def test_cache_upload(self):
        """Test a valid file upload to a cache ID."""
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        file_storage = self.make_test_file_storage(cache_id, token_id)
        minio.upload_cache(cache_id, token_id, file_storage)
        file_storage.stream.close()
        metadata = minio.get_metadata(cache_id)
        self.assertTrue(int(metadata['expiration']) > time.time(), 'Expiration is in the future')
        self.assertEqual(metadata['filename'], file_storage.filename, 'Correct filename is saved in the metadata')
        self.assertEqual(metadata['token_id'], token_id, 'Correct token ID is saved in the metadata')
        tmp_dir = tempfile.mkdtemp()
        save_path = minio.download_cache(cache_id, token_id, tmp_dir)
        with open(save_path, 'rb') as fd:
            saved_contents = fd.read().decode('utf-8')
            self.assertEqual(saved_contents, 'contents', 'Correct file contents uploaded')

    def test_cache_delete(self):
        """Test a valid file deletion."""
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        minio.delete_cache(cache_id, token_id)
        tmp_dir = tempfile.mkdtemp()
        with self.assertRaises(exceptions.MissingCache):
            minio.download_cache(cache_id, token_id, tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_unauthorized_download(self):
        """Test a download to the wrong token ID."""
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        tmp_dir = tempfile.mkdtemp()
        with self.assertRaises(exceptions.UnauthorizedAccess):
            minio.download_cache(cache_id, token_id + 'x', tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_unauthorized_upload(self):
        """Test an upload to the wrong token ID."""
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        file_storage = self.make_test_file_storage(cache_id, token_id)
        minio.create_placeholder(cache_id, token_id)
        with self.assertRaises(exceptions.UnauthorizedAccess):
            minio.upload_cache(cache_id, token_id + 'x', file_storage)
        file_storage.stream.close()

    def test_missing_cache_upload(self):
        """Test an upload to a missing cache ID."""
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        file_storage = self.make_test_file_storage(cache_id, token_id)
        minio.create_placeholder(cache_id, token_id)
        with self.assertRaises(exceptions.MissingCache):
            minio.upload_cache(cache_id + 'x', token_id, file_storage)
        file_storage.stream.close()

    def test_missing_cache_download(self):
        """Test a download to a missing cache ID."""
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        minio.create_placeholder(cache_id, token_id)
        tmp_dir = tempfile.mkdtemp()
        with self.assertRaises(exceptions.MissingCache):
            minio.download_cache(cache_id + 'x', token_id, tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_expire_entries(self):
        """
        Test that the expire_entries function removes expired files and does not remove non-expired
        files.
        """
        now = str(int(time.time()))
        token_id = 'url:user:name'
        cache_id = str(uuid4())
        metadata = {
            'filename': 'xyz.json',
            'expiration': now,  # quickly expires
            'token_id': token_id
        }
        with tempfile.NamedTemporaryFile(delete=True) as fd:
            minio.minio_client.fput_object(minio.bucket_name, cache_id, fd.name, metadata=metadata)
        (removed_count, total_count) = minio.expire_entries()
        self.assertTrue(removed_count >= 1, 'Removes at least 1 expired object.')
        self.assertTrue(total_count > 0, 'The bucket is non-empty.')
