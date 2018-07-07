# Caching Service Design Doc

## Purpose

Provide a generalized cache store that can be used from any other service, allowing users to avoid re-running expensive computation that has already been completed for the same dataset.

## MVP Specifications

**_Set a cache value_**

To set a cache value, send a POST request with content-type "multipart/form-data" (to facilitate the file upload).

The headers are:

* `Authorization` - required - authentication token for the service

The fields are:

* `json` - required - json options (see below)
* `file` - required - multipart form-data file to cache

The JSON options are
* `params` - required - an arbitrary set of data used in the cache's namespace
* `expiration_days` - optional - total time in days until the cache's file gets deleted

```
curl -i -X POST
  -H "Content-Type: multipart/form-data"
  -H "Authorization: token"
  -F file=@/home/u/bio.zip
  -F json="{\"expiration_days\": 30, \"params\": {<arbitrary_json_data>}}"
  https://<caching_service_url>/v1/set
```

If the cache succeeds, you will get back a 200 response with JSON indicating whether the cache was
created or updated (either `{"status": "created"}` or `{"status": "replaced"}`).

If your auth token is invalid, you will receive a 403. Otherwise, there should be no errors.

**_Request a cache value_**

To fetch a cache value, make a POST request to `/v1/get` with content-type
"application/json" and a field for "params":

```
curl -i -X POST
  -H "Content-Type: application/x-www-form-urlencoded"
  -H "Authorization: token"
  -d "{\"params\": {<arbitrary_json_data>}}"
  https://<caching_service_url>/v1/get
```

The service token and params JSON must exactly match those that you used when setting the cache in order to get the same file back.

If the cache file is found, then the server will response with a 200 and the URL of the cached file. Otherwise, the response will have status 404 with an empty body. A 403 response indicates that the service token is invalid. 

### Authentication

The cache service only accepts requests from other authorized services.

* The consumer service creates a unique identity with KBase's auth server.
* The caching service accepts the consumer's auth token and validates it with the auth server.

### Python client

In addition to a backend service, we can provide a simple Python client that makes it easy to upload large
files using a multipart streaming uploader.

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

* API stack: python, flask, and docker-compose
* Caching: Redis
* File storage: local at first, S3 or Minio later

### Cache location identifiers

Cache values are identified by:

* Service auth token
* Arbitrary set of JSON data representing the environment, module, parameters, user ID, etc. of your
  cache value. The consumer service that is using the caching service is responsible for this data structure.

The above data are concatenated into a single string, hashed, and then stored in Redis. Each hash
points to a file-path of the uploaded, cached file.

A separate key/value association stores an expiration, if present.

For example, we can store these key/value pairs in Redis:

* `cache_params_hash -> file_path`: cache location
* `expiration_days -> cache_params_hash`: expiration

