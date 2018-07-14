"""Exception classes used by the API routers."""


class InvalidContentType(Exception):
    """A value for a certain Content-Type header was invalid."""

    def __init__(self, invalid, correct):
        self.invalid = invalid
        self.correct = correct

    def __str__(self):
        return "Invalid Content-Type: '" + self.invalid + "'. Must be: '" + self.correct + "'."


class MissingHeader(Exception):
    """A certain required header is completely missing from a request."""

    def __init__(self, header_name):
        self.header_name = header_name

    def __str__(self):
        return "Missing header: " + self.header_name


class MissingCache(Exception):
    """A cache entry with cache_id is missing when it was expected to exist."""

    def __init__(self, cache_id):
        self.cache_id = cache_id

    def __str__(self):
        return "Unknown cache ID: " + self.cache_id


class UnauthorizedAccess(Exception):
    """An attempt to access a cache entry with the wrong token."""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
