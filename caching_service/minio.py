from minio import Minio
import time
import tempfile
import os
import io
import shutil
from werkzeug.utils import secure_filename
from caching_service.config import Config
import caching_service.exceptions as exceptions


minio_client = Minio(
    Config.minio_host,
    access_key=Config.minio_access_key,
    secret_key=Config.minio_secret_key,
    secure=Config.minio_https
)


# This is how metadata is stored in minio files for 'expiration' and 'filename'
# For example if you set the metadata 'xyz', then minio will store it as 'X-Amz-Meta-Xyz'
metadata_expiration_key = 'X-Amz-Meta-Expiration'
metadata_filename_key = 'X-Amz-Meta-Filename'
metadata_token_id_key = 'X-Amz-Meta-Token_id'


def create_placeholder(cache_id, token_id):
    """
    Create a placeholder file for a generated cache_id using a token_id. The metadata on this
    placeholder file can be used for later validating uploads.

    cache_id should be generated from caching_service.cache_id.generate_cache_id
    token_id hould be in the form of 'user:id'.
    """
    seven_days = 604800  # in seconds
    expiration = str(int(time.time() + seven_days))
    metadata = {
        'expiration': expiration,
        'filename': 'placeholder',
        'token_id': token_id
    }
    data = io.BytesIO()
    minio_client.put_object(Config.minio_bucket_name, cache_id, data, 0, metadata=metadata)


def authorize_access(cache_id, token_id):
    """
    Given a cache ID and token ID, authorize that the token has permission to access the cache.

    This will raise caching_service.exceptions.UnauthorizedCacheAccess if it is unauthorized.
    This will raise minio.error.NoSuchKey if the cache ID does not exist.
    """
    stat = minio_client.stat_object(Config.minio_bucket_name, cache_id)
    existing_token_id = stat.metadata[metadata_token_id_key]
    if token_id != existing_token_id:
        raise exceptions.UnauthorizedCacheAccess


def upload_cache(cache_id, token_id, file_storage):
    """
    Given a cache ID, file name, and file path, save all to minio.

    `file_storage` should be a flask FileStorage object (such as the one found in a flask file
    upload handler).
    """
    authorize_access(cache_id, token_id)
    # Delete any existing entries
    try:
        delete_cache(cache_id, token_id)
    except exceptions.MissingCache:  # TODO this should be a minio.error.ResponseError
        pass  # No old stuff to delete
    tmp_dir = tempfile.mkdtemp()
    filename = secure_filename(file_storage.filename)
    path = os.path.join(tmp_dir, filename)
    file_storage.save(path)
    # Save the cache metadata to leveldb
    thirty_days = 2592000  # in seconds
    # An int is better for serializing than a float
    expiration = str(int(time.time() + thirty_days))
    metadata = {
        'filename': filename,
        'expiration': expiration,
        'token_id': token_id
    }
    try:
        minio_client.fput_object(Config.minio_bucket_name, cache_id, path, metadata=metadata)
    finally:
        shutil.rmtree(tmp_dir)


def expire_entries():
    """
    Iterate over all expiration entries in the database, removing any expired caches.
    """
    # TODO each delete should be concurrent
    # TODO
    # now = time.time()
    # for key in db.scan_iter(expiration_prefix):
    #     expiry = db.get(key)
    #     cache_id = key.replace(expiration_prefix, '')
    #     if now > int(expiry):
    #         delete_entry(cache_id)
    pass


def delete_cache(cache_id, token_id):
    """Delete a cache entry in both leveldb and minio."""
    authorize_access(cache_id, token_id)
    minio_client.remove_object(Config.minio_bucket_name, cache_id)


def get_cache_filename(cache_id):
    """
    Given a cache ID, return the filename of the cached file.

    This may raise a minio.error.NoSuchKey (missing cache).
    """
    stat = minio_client.stat_object(Config.minio_bucket_name, cache_id)
    return stat.metadata[metadata_filename_key]


def download_cache(cache_id, token_id):
    """
    Download a file from a cache ID to a temp directory and path.

    Returns (save_path, parent_dir), which is both the path of the saved file and the path of the
    parent temp directory for cleanup.

    Note that this does not clean up the temp directory if the download succeeds; remove the temp
    directory after you are done with the file.

    This may raise an UnauthorizedCacheAccess or NoSuchKey (missing cache). If any unexpected error
    occurs, all temporary files will get cleaned up.
    """
    authorize_access(cache_id, token_id)
    tmp_dir = tempfile.mkdtemp()
    filename = get_cache_filename(cache_id)
    save_path = os.path.join(tmp_dir, filename)
    try:
        minio_client.fget_object(Config.minio_bucket_name, cache_id, save_path)
    except Exception as err:
        # Remove temporary files
        shutil.rmtree(tmp_dir)
        raise err
    return (save_path, tmp_dir)
