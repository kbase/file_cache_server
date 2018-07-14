"""User authorization utilities."""
import flask
import functools
import requests

from caching_service.config import Config
from caching_service.exceptions import MissingHeader, UnauthorizedAccess


def requires_service_token(fn):
    """
    Authorize that the requester is a valid, registered service on KBase.
    Validate a token passed in the 'Authorization' header.

    If valid, then set a session value to be the token's username and name.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = flask.request.headers.get('Authorization')
        if not token:
            raise MissingHeader('Authorization')
        headers = {'Authorization': token}
        url = Config.kbase_auth_url + '/api/V2/token'
        auth_resp = requests.get(url, headers=headers)
        auth_json = auth_resp.json()
        if 'error' in auth_json:
            raise UnauthorizedAccess(auth_json['error']['message'])
            resp = {'error': auth_json['error']['message'], 'status': 'error'}
            return (flask.jsonify(resp), 403)
        else:
            flask.session['token_id'] = auth_json['user'] + ':' + auth_json['name']
            return fn(*args, **kwargs)
    return wrapper
