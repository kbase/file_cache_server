"""The primary router for the Caching Service API v1."""
import json
import flask

from caching_service.authorization.service_token import requires_service_token
from caching_service.cache_id.generate_cache_id import generate_cache_id
import caching_service.api.exceptions as exceptions

api_v1 = flask.Blueprint('api_v1', __name__)


@api_v1.route('/', methods=['GET'])
def root():
    """Root route for the API which lists all paths."""
    resp = {
        'routes': {
            'root': 'GET /',
            'get_cache_id': 'POST /cache_id',
            'download_cache_file': 'GET /cache/<cache_id>',
            'upload_cache_file': 'POST /cache/<cache_id>'
        }
    }
    return flask.jsonify(resp)


@requires_service_token
@api_v1.route('/cache_id', methods=['POST'])
def get_cache_id():
    """Generate a cache ID from identifying data."""
    check_content_type('application/json')
    token = flask.request.headers.get('Authorization')
    json_body = get_json()
    json_text = json.dumps(json_body, sort_keys=True)
    cid = generate_cache_id(token, json_text)
    result = {'cache_id': cid, 'status': 'generated'}
    return flask.jsonify(result)


@requires_service_token
@api_v1.route('/cache/<cache_id>', methods=['GET'])
def download_cache_file(cache_id):
    result = {}  # type: dict
    return flask.jsonify(result)


@requires_service_token
@api_v1.route('/cache/<cache_id>', methods=['POST'])
def upload_cache_file(cache_id):
    result = {}  # type: dict
    return flask.jsonify(result)


# Error handlers
# --------------

@api_v1.errorhandler(exceptions.InvalidContentType)
@api_v1.errorhandler(exceptions.MissingHeader)
def invalid_content_type(err):
    result = {'status': 'error', 'error': str(err)}
    return (flask.jsonify(result), 422)


@api_v1.errorhandler(json.decoder.JSONDecodeError)
def invalid_json(err):
    result = {'status': 'error', 'error': 'JSON parsing error: ' + str(err)}
    return (flask.jsonify(result), 422)


# General, small route helpers
# ----------------------------

def check_content_type(correct):
    ct = flask.request.headers.get('Content-Type')
    if ct != 'application/json':
        raise exceptions.InvalidContentType(ct, 'application/json')


def get_json():
    json.loads(flask.request.data)  # Throws a JSONDecodeError
