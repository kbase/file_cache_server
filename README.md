# CachingService

Cache the results of running jobs on the KBase platform.

## References

* [Design document](docs/design.md)

## Development

### Running the server

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

### Tests

While the server is running, do:

```sh
$ docker-compose run web make test
```

### Project anatomy

* `app.py` is the main entrypoint for running the flask server
* `/caching_service/` is the main package directory
* `/caching_service/api` holds all the routes for every api version

_Pip Dependencies:_

* `requirements.txt` lists all pip requirements for running the server
* `dev-requirements.txt` lists all requirements for running the tests

If you install any new dependencies, be sure to re-run `docker-compose build`.

Docker:

* `docker-compose.yaml` and `/docker/Dockerfile-*` contain docker setup for all services

