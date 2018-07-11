
import os


class Config:
    """Global application configuration."""

    # Basic flask config
    secret_key = os.environ['SECRET_KEY']
    # Minio config data
    minio_host = os.environ['MINIO_HOST']
    minio_bucket_name = os.environ['MINIO_BUCKET_NAME']
    minio_access_key = os.environ['MINIO_ACCESS_KEY']
    minio_secret_key = os.environ['MINIO_SECRET_KEY']
    minio_https = os.environ.get('MINIO_SECURE', False)
    # LevelDB
    leveldb_path = os.environ.get('LEVELDB_PATH', '/tmp/leveldb')
