"""The primary router for the Caching Service API v1."""
import time
import subprocess  # nosec B404
import tempfile
import json
import flask
import minio.error
import shutil

from caching_service.authorization.service_token import requires_service_token
from caching_service.generate_cache_id import generate_cache_id
import caching_service.exceptions as exceptions
from caching_service.minio import (
    download_cache,
    upload_cache,
    create_placeholder,
    delete_cache
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
    return json_response(resp)


@api_v1.route('/cache_id', methods=['POST'])
@requires_service_token
def make_cache_id():
    """Generate a cache ID from identifying data."""
    check_content_type('application/json')
    check_header_present('Authorization')
    try:
        cid = generate_cache_id(flask.session['token_id'], get_json())
    except TypeError as err:
        result = {'status': 'error', 'error': str(err)}
        return json_response(result)
    metadata = create_placeholder(cid, flask.session['token_id'])
    result = {'cache_id': cid, 'status': 'ok', 'metadata': metadata}
    return json_response(result)


@api_v1.route('/cache/<cache_id>', methods=['GET'])
@requires_service_token
def download_cache_file(cache_id):
    """Fetch a file given a cache ID."""
    save_dir = tempfile.mkdtemp()
    path = download_cache(cache_id, flask.session['token_id'], save_dir)

    @flask.after_this_request
    def cleanup(response):
        """Remove temporary files when the request is completed."""
        shutil.rmtree(save_dir)
        return response
    return flask.send_file(path)


@api_v1.route('/cache/<cache_id>', methods=['POST'])
@requires_service_token
def upload_cache_file(cache_id):
    """Upload a file given a cache ID."""
    if 'file' not in flask.request.files:
        return (json_response({'status': 'error', 'error': 'File field missing'}), 400)
    f = flask.request.files['file']
    if not f.filename:
        return (json_response({'status': 'error', 'error': 'Filename missing'}), 400)
    upload_cache(cache_id, flask.session['token_id'], f)
    return json_response({'status': 'ok'})


@api_v1.route('/cache/<cache_id>', methods=['DELETE'])
@requires_service_token
def delete(cache_id):
    delete_cache(cache_id, flask.session['token_id'])
    return json_response({'status': 'ok'})


# Error handlers
# --------------

@api_v1.errorhandler(exceptions.MissingCache)
@api_v1.errorhandler(minio.error.NoSuchKey)
def missing_cache_file(err):
    """A cache ID was not found, but was expected to exist."""
    result = {'status': 'error', 'error': 'Cache ID not found'}
    return (json_response(result), 404)


# General, small route helpers
# ----------------------------

def check_content_type(correct):
    ct = flask.request.headers.get('Content-Type')
    if ct != 'application/json':
        raise exceptions.InvalidContentType(str(ct), 'application/json')


def check_header_present(name):
    if name not in flask.request.headers:
        raise exceptions.MissingHeader(name)


def get_json():
    return json.loads(flask.request.data)  # Throws a JSONDecodeError


def json_response(data):
    """Expand any json response with additional generic data."""
    args = ['git', 'rev-parse', '--short', 'HEAD']
    # Get the git commit hash (short) and strip the newline at the end
    git_commit_ver = subprocess.check_output(args)[0:-1]  # nosec B603, B607
    data.update({
        'ver': 1,
        'ver_hash': git_commit_ver,
        'response_timestamp': time.time()
    })
    return flask.jsonify(data)
