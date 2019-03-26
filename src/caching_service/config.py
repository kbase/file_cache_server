"""Global, static application configuration data stored in an object."""
from uuid import uuid4
import os


class Config:
    """Global application configuration."""

    # Basic flask config
    secret_key = os.environ.get('SECRET_KEY', str(uuid4()))
    # Minio config data
    minio_host = os.environ.get('MINIO_HOST', 'minio:9000')
    minio_bucket_name = os.environ.get('MINIO_BUCKET_NAME', 'kbase-cache')
    minio_access_key = os.environ.get('MINIO_ACCESS_KEY', 'minio')
    minio_secret_key = os.environ['MINIO_SECRET_KEY']
    minio_https = os.environ.get('MINIO_SECURE', False)
    # KBase authentication URL
    kbase_auth_url = os.environ.get('KBASE_AUTH_URL', 'http://auth:5000')
