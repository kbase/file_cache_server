"""A module to hash an arbitrary string using Blake2b."""

import nacl.encoding
import nacl.hash


def bhash(string):
    """
    Given any string, produce a hex-valued hash.

    The returned hash is a a utf-8 encoded normal string. Note that `hash` is a builtin function in
    Python. The hash will be 64 bytes long.
    """
    if not string or not isinstance(string, str):
        raise TypeError('Please provide a non-empty string')
    data = bytes(string, 'utf-8')
    mac = nacl.hash.blake2b(data, encoder=nacl.encoding.HexEncoder)
    return mac.decode('utf-8')
