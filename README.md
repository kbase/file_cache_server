# CachingService

Generic file-caching service for the KBase platform, allowing you to save the results of long-running jobs so you don't have repeat them unnecessarily.

_Typical workflow:_

1. Obtain a KBase authentication token (you will use this for all cache operations).
2. Create a cache ID using your auth token and some unique identifiers for your cache (such as method names and parameters)
3. Upload, download, and delete a cache file with the cache ID

The KBase auth token is used to scope caches. Use a unique auth token for each consumer service that uses the cache server.

A **cache ID** is a unique ID that represents your auth token and a set of arbitrary JSON data that identifies the cache file (such as method name and method params). Generating an ID is fast and cheap; you can re-generate a cache ID every time you use the cache. You do not need to store cache IDs.

#### Expirations

Cache files expire after 30 days of inactivity. If the file is not downloaded or replaced within 30 days, it will get deleted.

After generating a cache ID, you have 7 days to upload a file using the ID, after which the ID will expire and you will have to re-generate it.

## API

### Create cache ID

* Path: `/v1/cache_id`
* Method: `POST`
* Required headers:
  * `Content-Type` must be `application/json`
  * `Authorization` must be your service token
* Body: arbitrary JSON data that identifies your cache

Sample request:

```sh
curl -X POST
     -H "Content-Type: application/json"
     -H "Authorization: <service_auth_token>"
     -d '{"method_name": "mymethod", "params": {"contig_length": 123}}'
     https://<caching_service_host>/v1/cache_id
```

Sample successful response:

```
{
  "cache_id": "xyzxyz",
  "status": "created"
}
```

Sample failed response:

```
{
  "status": "error",
  "error": "Message describing what went wrong"
}
```

Use the cache ID for requests to upload/download/delete caches. Cache IDs can be re-generated any number of times.

Note that cache IDs expire after 7 days if unused.

### Upload a cache file

* Path: `/v1/cache/<cache_id>`
* Method: `POST`
* Required headers:
  * `Content-Type` should be `multipart/form-data`
  * `Authorization` must be your service token
* Body: multipart file upload data using the `'file'` field

Sample request:

```sh
curl -X POST
     -H "Content-Type: multipart/form-data"
     -H "Authorization: <service_auth_token>"
     -F "file=@myfile.zip"
     https://<caching_service_host>/v1/cache/<cache_id>
```

Sample successful response:

```sh
{"status": "created"}
```

Sample failed response:

```sh
{
  "status": "error",
  "error": "Message describing what went wrong"
}
```

### Download a cache file

* Path: `/v1/cache/<cache_id>`
* Method: `GET`
* Required headers:
  * `Authorization` must be your service token

Sample request:

```sh
curl -X GET
     -H "Authorization: <service_auth_token>"
     -F "file=@myfile.zip"
     https://<caching_service_host>/v1/cache/<cache_id>
```

A successful response will give you the complete file data with the content type of what you uploaded.

Failed responses will return JSON:

```sh
{
  "status": "error",
  "error": "Message describing what went wrong"
}
```

### Delete a cache file

* Path: `/v1/cache/<cache_id>`
* Method: `DELETE`
* Required headers:
  * `Authorization` must be your service token

Sample request:

```sh
curl -X DELETE
     -H "Authorization: <service_auth_token>"
     https://<caching_service_host>/v1/cache/<cache_id>
```

Sample successful response:

```sh
{"status": "deleted"}
```

Sample failed response:

```sh
{
  "status": "error",
  "error": "Message describing what went wrong"
}
```

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

Set an env var for `KBASE_AUTH_TOKEN` before running the tests (you can put this in your `.env` file).

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
* `/caching_service/minio.py` contains utils for uploading, checking, and fetching files with Minio
* `/caching_service/cache_id/` contains utils for generating cache IDs from tokens/params
* `/caching_service/api` holds all the routes for each api version
* `/caching_service/hash.py` is a utility wrapping pynacl (which uses libsodium) to do blake2b hashing
* `/caching_service/authorization/` contains utilites for authorization using KBase's auth service

_Dependencies:_

This project makes heavy use of [Minio](https://docs.minio.io/) using the Python Minio client.

* `requirements.txt` lists all pip requirements for running the server
* `dev-requirements.txt` lists all requirements for running the tests

If you install any new dependencies, be sure to re-run `docker-compose build`.

Docker:

* `docker-compose.yaml` and `/docker/Dockerfile-*` contain docker setup for all services


## References

* [Design document](docs/design.md)
