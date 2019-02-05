"""A module to hash an arbitrary string using Blake2b."""

import hashlib


def bhash(string):
    """
    Given any string, produce a hex-valued hash.
    Docs on blake2b: https://docs.python.org/3/library/hashlib.html#hashlib.blake2b
    """
    if not string or not isinstance(string, str):
        raise TypeError('Please provide a non-empty string')
    return hashlib.blake2b(string.encode()).hexdigest()
