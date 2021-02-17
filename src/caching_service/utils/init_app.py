"""
Any initialization code that needs to be run before any workers start:
    - wait for Minio to be healthy
    - create the bucket
"""
import src.caching_service.minio as minio


def init_app():
    # Wait for minio to be healthy
    minio.wait_for_service()
    minio.initialize_bucket()


if __name__ == '__main__':
    init_app()
