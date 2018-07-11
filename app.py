"""The main entrypoint for running the Flask server."""
import flask
import os

from caching_service.api.api_v1 import api_v1
from caching_service.config import Config

app = flask.Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', True)
app.config['SECRET_KEY'] = Config.secret_key

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


@app.teardown_request
def close_db(response):
    """Close the leveldb connection when the request is complete."""
    if hasattr(flask.g, 'db'):
        flask.g.db.close()
