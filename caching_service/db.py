"""Get a database connection instance."""
import plyvel
from contextlib import contextmanager

from caching_service.config import Config


@contextmanager
def open_db():
    """Initialize or retrieve the db connection using a flask global."""
    db = plyvel.DB(Config.leveldb_path, create_if_missing=True)
    yield db
    db.close()
