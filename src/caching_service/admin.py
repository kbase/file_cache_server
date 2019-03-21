"""Caching service basic administration commands.

Usage:
    admin.py expire_all

Commands:
    expire_all    Find all expired caches and remove them
"""

from docopt import docopt

from .minio import expire_entries


if __name__ == '__main__':
    args = docopt(__doc__, help=True)
    if args['expire_all']:
        expire_entries()
