from minio import Minio
import time

from caching_service.get_db import get_db
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


def upload_file(cache_id, filename, local_path):
    """
    Given a cache ID, file name, and file path, save all to minio/db.
    """
    db = get_db()
    # Save the cache metadata to leveldb
    thirty_days = 2592000  # in seconds
    # An int is better to serialize in the db than a float
    expiration = str(int(time.time() + thirty_days))
    minio_path = cache_id + '/' + filename
    filename_key = (filename_prefix + cache_id).encode()
    expiration_key = (expiration_prefix + cache_id).encode()
    db.put(filename_key, filename.encode())
    db.put(expiration_key, expiration.encode())
    minio_client.fput_object(Config.minio_bucket_name, minio_path, local_path)


def expire_entries():
    """
    Iterate over all expiration entries in the database, removing any expired caches.
    """
    db = get_db()
    now = time.time()
    for key, expiry in db.iterator(prefix=expiration_prefix.encode()):
        cache_id = key.decode('utf-8').replace(expiration_prefix, '')
        if now > int(expiry):
            delete_entry(cache_id)


def delete_entry(cache_id):
    """Delete a cache entry in both leveldb and minio."""
    db = get_db()
    filename_key = (filename_prefix + cache_id).encode()
    expiry_key = (expiration_prefix + cache_id).encode()
    filename_bytes = db.get(filename_key)
    if not filename_bytes:
        raise exceptions.MissingCache(cache_id)
    filename = db.get(filename_key).decode('utf-8')
    minio_path = cache_id + '/' + filename
    minio_client.remove_object(Config.minio_bucket_name, minio_path)
    db.delete(filename_key)
    db.delete(expiry_key)


def download_file(cache_id):
    # First read the metadata to get the minio_path
    # TODO this should be a streamer -- dont save anything to disk
    db = get_db()
    key = (filename_prefix + cache_id).encode()
    filename_bytes = db.get(key)
    if not filename_bytes:
        raise exceptions.MissingCache(cache_id)
    filename = filename_bytes.decode('utf-8')
    local_path = '/tmp/' + filename
    minio_path = cache_id + '/' + filename
    minio_client.fget_object(Config.minio_bucket_name, minio_path, local_path)
    return local_path
