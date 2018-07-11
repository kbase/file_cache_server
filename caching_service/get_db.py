"""Get a database connection instance."""
import plyvel
import flask

from caching_service.config import Config


def get_db():
    """Initialize or retrieve the db connection using a flask global."""
    with flask.current_app.app_context():
        if not hasattr(flask.g, 'db'):
            flask.g.db = plyvel.DB(Config.leveldb_path, create_if_missing=True)
        return flask.g.db
