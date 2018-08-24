# Caching Service Design Doc

## Purpose

Provide a generalized cache store that can be used from any other service, allowing users to avoid re-running expensive computation that has already been completed for the same dataset.

The time to download a file should be shorter than the time it takes to generate that file. This is useful for cases where it takes a long time to generate a relatively small file.

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

* `"status"` - "ok" | "error" - whether a file has been uploaded for this cache ID or not, or whether there was an error generating the ID.
* `"id"`- the cache ID (plain string)
* `"error"` - if "status" is "error", this will contain an error message

An invalid service token will give a response status of 403, while other errors will give appropriate error status codes.

**_Upload a file with a cache ID_**

Post file data to the path `/cache/<cache_id>`. Use the `multipart/form-data` content type

Headers:
* `Authorization` - required - service token
* `Content-Type` - required - should be `multipart/form-data`

A successful response will have JSON fields for:

* `"status"` - "ok" | "error". Whether the request was successful, or there was an error
* `"error"` - if the status is "error", this will contain an error message

An invalid service token will give a response status of 403, while other errors will give appropriate error status codes.

```sh
curl -X POST
  -H "Content-Type: multipart/form-data"
  -H "Authorization: <service_token>"
  -F "file=@/home/user/my-file.txt"
```

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

## Design

_Tools_

* API stack: python, flask/gunicorn, and docker-compose
* File storage: Minio

### Cache location identifiers

Cache entries are identified by:

* Username that generated the provided auth token
* Arbitrary set of identifying JSON data representing the environment, module, parameters, user ID, etc. of your
  cache value.

The above data are concatenated into a single string and hashed to form a secure, uniform, private ID that points to the cache file.

### Expiration

Expiration is stored as file metadata in each Minio cache object. 

A very simple admin CLI can be used to remove all expired entries in the Minio bucket.
