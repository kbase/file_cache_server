# CachingService

Cache the results of running jobs on the KBase platform.

## References

* [Design document](docs/design.md)

## Development

### Environment setup

Create a file called `.env` in the root of the project with the following values:

```
SECRET_KEY=xyz
MINIO_SECRET_KEY=minio123
MINIO_ACCESS_KEY=minio
MINIO_HOST=localhost:9000
MINIO_BUCKET_NAME=kbase-cache
```

### Building and running

With Docker and docker-compose installed, simply do:

```sh
$ docker-compose up
```

If your docker build becomes corrupted and you're having a hard time troubleshooting, try doing a
hard reset:

```sh
$ docker-compose rm
$ docker-compose build --no-cache
$ docker-compose up
```

### Bucket setup

Before the cache can work, you need to manually create a bucket called "kbase-cache" (matching the
`"MINIO_BUCKET_NAME"` env var):

Open up `localhost:9000` and create the bucket in the Minio web UI while the server is running.

### Tests

While the server is running, do:

```sh
$ docker-compose run web make test
```

### Project anatomy

* `app.py` is the main entrypoint for running the flask server
* `/caching_service/` is the main package directory
* `/caching_service/minio/` contains utils for uploading, checking, and fetching files with Minio
* `/caching_service/cache_id/` contains utils for generating cache IDs from tokens/params
* `/caching_service/api` holds all the routes for every api version
* `/caching_service/hash.py` is a utility wrapping pynacl (which uses libsodium) to do blake2b hashing

_Pip Dependencies:_

* `requirements.txt` lists all pip requirements for running the server
* `dev-requirements.txt` lists all requirements for running the tests

If you install any new dependencies, be sure to re-run `docker-compose build`.

Docker:

* `docker-compose.yaml` and `/docker/Dockerfile-*` contain docker setup for all services

