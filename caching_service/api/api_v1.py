"""The primary router for the Caching Service API v1."""
import flask
import functools

api_v1 = flask.Blueprint('api_v1', __name__)


def requires_user(fn):
    """
    Authorize that the requester is a signed-in user.

    This is a decorator function that can wrap a route function.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        authorized = True  # TODO
        if authorized:
            resp = {'error': 'Unauthorized'}
            return flask.jsonify(resp, 301)
        else:
            return fn(*args, **kwargs)
    return wrapper


@api_v1.route('/', methods=['GET'])
def root():
    """Root route for the API which lists all paths."""
    resp = {
        'routes': {
            'root': 'GET /'
        }
    }
    return flask.jsonify(resp)


@requires_user
@api_v1.route('/post_test', methods=['POST'])
def test():
    """Test post request."""
    return flask.jsonify({'test': 123})
