from minio import Minio
import minio.error
import time
import tempfile
import os
import io
import requests
import shutil
from werkzeug.utils import secure_filename

from .config import Config
from . import exceptions


# Initialize the Minio client object using the app's configuration
minio_client = Minio(
    Config.minio_host,
    access_key=Config.minio_access_key,
    secret_key=Config.minio_secret_key,
    secure=Config.minio_https
)
bucket_name = Config.minio_bucket_name


def initialize_bucket():
    """
    Create the default bucket if it does not exist
    """
    try:
        print('making bucket', bucket_name)
        minio_client.make_bucket(bucket_name)
        print('done making bucket', bucket_name)
    except minio.error.S3Error as err:
        # Acceptable errors
        errs = ["BucketAlreadyExists", "BucketAlreadyOwnedByYou"]
        if err.code not in errs:
            raise err


def wait_for_service():
    """
    Wait for the minio service to be healthy
    """
    url = f'http://{Config.minio_host}/minio/health/live'
    max_time = 180
    start = time.time()
    while True:
        try:
            requests.get(url).raise_for_status()
            print("Minio is healthy! Continuing.")
            break
        except Exception as err:
            if time.time() > start + max_time:
                raise RuntimeError("Timed out waiting for Minio")
            print(f"Still waiting for Minio at {url} to be healthy:")
            print(err)


def create_placeholder(cache_id, token_id):
    """
    Create a placeholder file for a generated cache_id using a token_id. The metadata on this
    placeholder file can be used for later validating uploads and checking expirations.

    If a placeholder has already been created, but no file uploaded, then no action is taken and
    'empty' is returned. If a cached file already exists, then no action is taken and 'file_exists'
    is returned. If nothing at all exists at that cache ID, then the placeholder is created and
    'empty' is returned.

    cache_id should be generated from caching_service.cache_id.generate_cache_id
    token_id hould be in the form of 'user:id'.

    Returns one of "file_exists" or "empty", indicating whether that cache_id holds a saved file or is empty.
    """
    try:
        return get_metadata(cache_id)
    except exceptions.MissingCache:
        # Create the cache key
        seven_days = 604800  # in seconds
        expiration = str(int(time.time() + seven_days))
        metadata = {
            'expiration': expiration,
            'filename': 'placeholder',
            'token_id': token_id
        }
        data = io.BytesIO()  # Empty contents for placeholder cache
        minio_client.put_object(bucket_name, cache_id, data, 0, metadata=metadata)
        return metadata


def authorize_access(cache_id, token_id):
    """
    Given a cache ID and token ID, authorize that the token has permission to access the cache.

    Raises:
        - caching_service.exceptions.UnauthorizedAccess if it is unauthorized.
        - exceptions.MissingCache if the cache ID does not exist.
    """
    metadata = get_metadata(cache_id)
    existing_token_id = metadata['token_id']
    if token_id != existing_token_id:
        raise exceptions.UnauthorizedAccess('You do not have access to that cache')


def upload_cache(cache_id, token_id, file_storage):
    """
    Given a cache ID, file name, and file path, save all to minio.

    `file_storage` should be a flask FileStorage object (such as the one found in a flask file
    upload handler).
    """
    authorize_access(cache_id, token_id)
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
        minio_client.fput_object(bucket_name, cache_id, path, metadata=metadata)
    finally:
        shutil.rmtree(tmp_dir)


def expire_entries():
    """
    Iterate over all expiration metadata for every file in the cache bucket, removing any expired caches.
    """
    print('Checking the expiration of all stored objects..')
    now = time.time()
    objects = minio_client.list_objects(bucket_name)
    removed_count = 0
    total_count = 0
    for obj in objects:
        # It seems that the Minio client does not return metadata when listing objects
        # Issue here: https://github.com/minio/minio-py/issues/679
        # We have to fetch it separately
        total_count += 1
        metadata = get_metadata(obj.object_name)
        if not metadata or ('expiration' not in metadata):
            minio_client.remove_object(bucket_name, obj.object_name)
            removed_count += 1
        else:
            expiry = int(metadata.get('expiration'))
            if now > expiry:
                minio_client.remove_object(bucket_name, obj.object_name)
                removed_count += 1
    print('... Finished running. Total objects: {}. Removed {} objects'.format(total_count, removed_count))
    return (removed_count, total_count)


def delete_cache(cache_id, token_id):
    """Delete a cache entry in both leveldb and minio."""
    authorize_access(cache_id, token_id)
    minio_client.remove_object(bucket_name, cache_id)


def get_metadata(cache_id):
    """Return the Minio metadata dict for a cache file."""
    try:
        orig_metadata = minio_client.stat_object(bucket_name, cache_id).metadata
    except minio.error.S3Error as err:
        # Catch NoSuchKey errors and raise MissingCache
        if err.code != "NoSuchKey":
            raise err
        raise exceptions.MissingCache(cache_id)
    # The below keys are how metadata gets stored in minio files for 'expiration', 'filename', etc
    # For example if you set the metadata 'xyz_abc', then minio will store it as 'X-Amz-Meta-Xyz_abc'
    return {
        'expiration': orig_metadata['X-Amz-Meta-Expiration'],
        'filename': orig_metadata['X-Amz-Meta-Filename'],
        'token_id': orig_metadata['X-Amz-Meta-Token_id']
    }


def download_cache(cache_id, token_id, save_dir):
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
    metadata = get_metadata(cache_id)
    filename = metadata['filename']
    if not filename or filename == 'placeholder':
        raise exceptions.MissingCache(cache_id)
    save_path = os.path.join(save_dir, filename)
    minio_client.fget_object(Config.minio_bucket_name, cache_id, save_path)
    return save_path
