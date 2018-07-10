from minio import Minio
import minio.error

from caching_service.config import Config


minio_client = Minio(
    Config.minio_host,
    access_key=Config.minio_access_key,
    secret_key=Config.minio_secret_key,
    secure=Config.minio_https
)


def upload_file(cache_id, path):
    try:
        minio_client.fput_object(Config.minio_bucket_name, cache_id, path)
    except minio.error.ResponseError as err:
        print(err)


def download_file(cache_id):
    path = '/tmp/' + cache_id
    # First read the metadata
    try:
        minio_client.fget_object(Config.minio_bucket_name, cache_id, path)
        return path
    except minio.error.ResponseError as err:
        print(err)
