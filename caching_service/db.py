"""Get a database connection instance."""
import plyvel
from contextlib import contextmanager
from plyvel._plyvel import IOError

from caching_service.config import Config


@contextmanager
def open_db():
    """Initialize or retrieve the db connection using a flask global."""
    db = _init_db()
    yield db
    db.close()


@contextmanager
def open_db_batch():
    """Open a db connection for batch writing (put or delete)."""
    db = _init_db()
    batch = db.write_batch()
    yield (db, batch)
    batch.write()
    db.close()


def _init_db():
    """Initialize the DB with a simple loop to wait for a connection."""
    is_locked = True
    while is_locked:
        try:
            db = plyvel.DB(Config.leveldb_path, create_if_missing=True)
            is_locked = False
        except IOError:
            pass
    return db
