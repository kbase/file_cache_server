"""The primary router for the Caching Service API v1."""
import json
import flask
import minio.error
import shutil

from caching_service.authorization.service_token import requires_service_token
from caching_service.cache_id.generate_cache_id import generate_cache_id
import caching_service.exceptions as exceptions
from caching_service.minio.main import (
    download_file,
    upload_file,
    delete_entry
)

api_v1 = flask.Blueprint('api_v1', __name__)


@api_v1.route('/', methods=['GET'])
def root():
    """Root route for the API which lists all paths."""
    resp = {
        'routes': {
            'root': 'GET /',
            'generate_cache_id': 'POST /cache_id',
            'download_cache_file': 'GET /cache/<cache_id>',
            'upload_cache_file': 'POST /cache/<cache_id>',
            'delete_cache_file': 'DELETE /cache/<cache_id>'
        }
    }
    return flask.jsonify(resp)


@requires_service_token
@api_v1.route('/cache_id', methods=['POST'])
def make_cache_id():
    """Generate a cache ID from identifying data."""
    check_content_type('application/json')
    check_header_present('Authorization')
    token = flask.request.headers.get('Authorization')
    cid = generate_cache_id(token, get_json())
    result = {'cache_id': cid, 'status': 'generated'}
    return flask.jsonify(result)


@requires_service_token
@api_v1.route('/cache/<cache_id>', methods=['GET'])
def download_cache_file(cache_id):
    """Fetch a file given a cache ID."""
    (path, parent_dir) = download_file(cache_id)

    @flask.after_this_request
    def cleanup(response):
        # Remove temporary files when the request is completed.
        shutil.rmtree(parent_dir)
        return response
    return flask.send_file(path)


@requires_service_token
@api_v1.route('/cache/<cache_id>', methods=['POST'])
def upload_cache_file(cache_id):
    """Upload a file given a cache ID."""
    if 'file' not in flask.request.files:
        return (flask.jsonify({'status': 'error', 'error': 'File field missing'}), 400)
    f = flask.request.files['file']
    if not f.filename:
        return (flask.jsonify({'status': 'error', 'error': 'Filename missing'}), 400)
    upload_file(cache_id, f)
    return flask.jsonify({'status': 'saved'})


# @api_v1.route('/expire_all', methods=['POST'])
# def expire_all():
#     # TODO remove this endpoint
#     result = expire_entries()
#     return flask.jsonify(result)


@api_v1.route('/cache/<cache_id>', methods=['DELETE'])
def delete(cache_id):
    # TODO remove this endpoint
    delete_entry(cache_id)
    return flask.jsonify({'status': 'deleted'})


# Error handlers
# --------------

@api_v1.errorhandler(exceptions.MissingCache)
@api_v1.errorhandler(minio.error.NoSuchKey)
def missing_cache_file(err):
    """A cache ID was not found, but was expected to exist."""
    result = {'status': 'error', 'error': 'Cache ID not found'}
    return flask.jsonify(result)


# General, small route helpers
# ----------------------------

def check_content_type(correct):
    ct = flask.request.headers.get('Content-Type')
    if ct != 'application/json':
        raise exceptions.InvalidContentType(ct, 'application/json')


def check_header_present(content_type):
    if not flask.request.headers.get('Authorization'):
        raise exceptions.MissingHeader('Authorization')


def get_json():
    return json.loads(flask.request.data)  # Throws a JSONDecodeError
