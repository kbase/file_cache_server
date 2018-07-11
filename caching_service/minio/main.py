from minio import Minio
import time
import tempfile
import os
import shutil
from werkzeug.utils import secure_filename

from caching_service.db import open_db, open_db_batch
from caching_service.config import Config
import caching_service.exceptions as exceptions


minio_client = Minio(
    Config.minio_host,
    access_key=Config.minio_access_key,
    secret_key=Config.minio_secret_key,
    secure=Config.minio_https
)


# Leveldb key prefixes
expiration_prefix = 'expiration:'
filename_prefix = 'filename:'


def upload_file(cache_id, file_storage):
    """
    Given a cache ID, file name, and file path, save all to minio/db.

    `file_storage` should be a flask FileStorage object (such as the one found in a flask file
    upload handler).
    """
    # Delete any existing entries
    try:
        delete_entry(cache_id)
    except exceptions.MissingCache:
        pass  # No old stuff to delete
    tmp_dir = tempfile.mkdtemp()
    filename = secure_filename(file_storage.filename)
    path = os.path.join(tmp_dir, filename)
    file_storage.save(path)
    # Save the cache metadata to leveldb
    thirty_days = 2592000  # in seconds
    # An int is better for serializing in the db than a float
    expiration = str(int(time.time() + thirty_days))
    filename_key = (filename_prefix + cache_id).encode()
    expiration_key = (expiration_prefix + cache_id).encode()
    with open_db_batch() as (db, batch):
        batch.put(filename_key, filename.encode())
        batch.put(expiration_key, expiration.encode())
    minio_path = cache_id + '/' + filename
    try:
        minio_client.fput_object(Config.minio_bucket_name, minio_path, path)
    finally:
        shutil.rmtree(tmp_dir)


def expire_entries():
    """
    Iterate over all expiration entries in the database, removing any expired caches.
    """
    # TODO each delete should be concurrent
    now = time.time()
    with open_db() as db:
        for key, expiry in db.iterator(prefix=expiration_prefix.encode()):
            cache_id = key.decode('utf-8').replace(expiration_prefix, '')
            if now > int(expiry):
                delete_entry(cache_id)


def delete_entry(cache_id):
    """Delete a cache entry in both leveldb and minio."""
    filename_key = (filename_prefix + cache_id).encode()
    expiry_key = (expiration_prefix + cache_id).encode()
    with open_db_batch() as (db, batch):
        filename_bytes = db.get(filename_key)
        if not filename_bytes:
            raise exceptions.MissingCache(cache_id)
        filename = db.get(filename_key).decode('utf-8')
        minio_path = cache_id + '/' + filename
        minio_client.remove_object(Config.minio_bucket_name, minio_path)
        batch.delete(filename_key)
        batch.delete(expiry_key)


def get_cache_filename(cache_id):
    """Given a cache ID, return a path for the file. If not found, then raises a MissingCache exception."""
    key = (filename_prefix + cache_id).encode()
    with open_db() as db:
        filename_bytes = db.get(key)
    if not filename_bytes:
        raise exceptions.MissingCache(cache_id)
    return filename_bytes.decode('utf-8')


def download_file(cache_id):
    """
    Download a file from a cache ID to a given path with a given filename.

    Returns (save_path, parent_dir), which is both the path of the saved file and the path of the
    parent temp directory for cleanup.

    Note that this does not clean up the temp directory if the download succeeds; remove the temp
    directory after you are done with the file.
    """
    tmp_dir = tempfile.mkdtemp()
    filename = get_cache_filename(cache_id)
    save_path = os.path.join(tmp_dir, filename)
    minio_path = cache_id + '/' + filename
    try:
        minio_client.fget_object(Config.minio_bucket_name, minio_path, save_path)
    except Exception as err:
        # Remove temporary files
        shutil.rmtree(tmp_dir)
        raise err
    return (save_path, tmp_dir)
