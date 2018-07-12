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

If your docker build becomes corrupted and you're having a hard time troubleshooting, try doing a hard reset:

```sh
$ docker-compose down --rmi all -v --remove-orphans
$ docker-compose build --no-cache
$ docker-compose up
```

### Bucket setup

Before the cache can work, you need to manually create a bucket called "kbase-cache" (or anything else matching the `"MINIO_BUCKET_NAME"` env var):

Open up `localhost:9000` and create the bucket in the Minio web UI while the server is running.

#### Delete a whole bucket

To delete an entire non-empty bucket, run:

```sh
$ docker-compose run mc rm -r --force /data/kbase-cache
```

Where `kbase-cache` is the name of the bucket you want to delete. **This also deletes the bucket itself, so make sure to recreate the bucket when you start the server again.**

### Tests

While the server is running, do:

```sh
$ docker-compose run web make test
```

#### Stress tests

There is a test class for stress-testing the server in `test/test_server_stress.py`. Run it with:

```sh
$ docker-compose run web make stress_test
```

It makes a large number of parallel requests (1000 total) to the server to upload/download/delete small files.
It also uploads and deletes two 1gb files in parallel.

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

