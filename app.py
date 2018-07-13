"""The main entrypoint for running the Flask server."""
import flask
import os
import traceback
from werkzeug.exceptions import MethodNotAllowed
from json.decoder import JSONDecodeError

from caching_service.api.api_v1 import api_v1
from caching_service.exceptions import MissingHeader, InvalidContentType
from caching_service.config import Config

app = flask.Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', True)
app.config['SECRET_KEY'] = Config.secret_key
app.url_map.strict_slashes = False  # allow both `get /v1/` and `get /v1`

app.register_blueprint(api_v1, url_prefix='/v1')


@app.route('/', methods=['GET'])
def root():
    """Root path for the entire service; lists all API endpoints."""
    return flask.jsonify({
        'endpoints': {
            'api_v1': {
                'path': '/v1',
                'desc': 'API Version 1',
                'example': 'GET /v1'
            }
        }
    })


@app.errorhandler(Exception)
def general_exception_handler(err):
    """General exception handler; catch any exception from anywhere."""
    print('=' * 80)
    print('500 Unexpected Server Error')
    print('-' * 80)
    traceback.print_exc()
    print('=' * 80)
    result = {'status': 'error', 'error': 'Unexpected server error'}
    return (flask.jsonify(result), 500)


@app.errorhandler(MethodNotAllowed)
def method_not_allowed(err):
    """A request has been made to a valid path with an invalid method."""
    result = {'status': 'error', 'error': 'Method not allowed'}
    return (flask.jsonify(result), 405)


@app.errorhandler(JSONDecodeError)
def invalid_json(err):
    """There has been a problem in a request in trying to parse JSON."""
    result = {'status': 'error', 'error': 'JSON parsing error: ' + str(err)}
    return (flask.jsonify(result), 400)


@app.errorhandler(MissingHeader)
@app.errorhandler(InvalidContentType)
def missing_header(err):
    """Other user-generated request problems."""
    result = {'status': 'error', 'error': str(err)}
    return (flask.jsonify(result), 400)


@app.after_request
def log_response(response):
    """Simple log of each request's response."""
    print(' '.join([flask.request.method, flask.request.path, '->', response.status]))
    return response
