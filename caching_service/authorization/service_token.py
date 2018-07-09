"""User authorization utilities."""
import flask
import functools

from caching_service.api.exceptions import MissingHeader


def requires_service_token(fn):
    """
    Authorize that the requester is a valid, registered service on KBase.

    This is a decorator function that can wrap a route function.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = flask.request.headers.get('Authorization')
        if not token:
            raise MissingHeader('Authorization')
        authorized = True  # TODO
        if authorized:
            resp = {'error': 'Unauthorized'}
            return flask.jsonify(resp, 403)
        else:
            return fn(*args, **kwargs)
    return wrapper
