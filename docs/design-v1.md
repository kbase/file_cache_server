# Caching Service Design Doc

## Purpose

Provide a generalized cache store that can be used from any other service, allowing users to avoid re-running expensive computation that has already been completed for the same dataset.

## MVP Specifications

**_Generate/fetch a cache ID_**

Every entry in the cache has an ID, which is generated from a service token and arbitrary JSON data. To generate a new cache ID, make a post request to `/cache_id`.

Headers:

* `Content-Type` - required - "application/json"
* `Authorization` - required - a service token

The request body should be an arbitrary JSON data structure that uniquely identifies the file you are caching (eg. the method name and all the parameter data that was used to generate the file).

```sh
curl -X POST
  -H "Content-Type: application/json"
  -H "Authorization: <service_token>"
  -d "{\"method_name\": "my_method", \"params\": {\"assembly_ref\": \"xyz\", \"min_length\": 500}}"
  https://<caching_service_url/<version>/cache_id
```

The response will include the following JSON fields:

* `"status"` - "file_exists" | "no_file" | "error" - whether a file has been uploaded for this cache ID or not, or whether there was an error generating the ID.
* `"id"`- the cache ID (plain string)
* `"error"` - if "status" is "error", this will contain an error message

An invalid service token will give a response status of 403, while other errors will give appropriate error status codes.

**_Upload a file with a cache ID_**

Post file data to the path `/cache/<cache_id>`. Use a content-type matching the file, such as `application/zip` or `application/octet-stream`.

Headers:
* `Authorization` - required - service token
* `Content-Type` - required - content type of your file (such as `application/zip`)
* `Content-Length` - required - length in bytes of the file

A successful response will have JSON fields for:

* `"status"` - "created" | "replaced" | "error". Whether a new file was created, a replacement was made, or there was an error
* `"error"` - if the status is "error", this will contain an error message

An invalid service token will give a response status of 403, while other errors will give appropriate error status codes.

**_Fetch a cached file_**

Make a get request to `/cache/<cache_id>` to download a file for a cache.

```sh
curl -X GET
  https://<caching_service_url>/<version>/cache/<cache_id>
```

### Authentication

The cache service only accepts requests from other authorized services.

* The consumer service creates a unique identity with KBase's auth server.
* The caching service accepts the consumer's auth token and validates it with the auth server.

Cache IDs are hashes that include the service token. Since service tokens are private, no two
services can ever generate or guess the cache ID used by another service.

### Python client

In addition to a backend service, we can provide a simple Python client that makes it easy to upload large
files using a streaming uploader/downloader.

```py
from kbase_caching_client import Cache

cache = Cache({'service': 'MyService', 'token': 'xyz'})

cache_params = {
  'method': 'my_method',
  'params': method_params
}

with cache(cache_params) as file:
  # this block is only run when the cache is missing
  file.write('xyz')
  # When this block is completed, the file is cached, all IO is closed

```

## Design

_Tools_

* API stack: python, flask/gunicorn, and docker-compose
* File storage: S3

### Cache location identifiers

Cache entries are identified by:

* Service auth token
* Arbitrary set of identifying JSON data representing the environment, module, parameters, user ID, etc. of your
  cache value.

The above data are concatenated into a single string and hashed to form a secure, uniform, private ID that points to the cache file.

### Expiration

We use an S3 bucket policy to expire any cached file. The simplest strategy is to have a global expiration policy such as:

* An object expires if it has not been accessed in 30 days
