"""Exception classes used by the API routers."""


class InvalidContentType(Exception):

    def __init__(self, invalid, correct):
        self.invalid = invalid
        self.correct = correct

    def __str__(self):
        return "Invalid Content-Type: '" + self.invalid + "'. Must be: '" + self.correct + "'."


class MissingHeader(Exception):

    def __init__(self, header_name):
        self.header_name = header_name

    def __str__(self):
        return "Missing header: " + self.header_name


class MissingCache(Exception):

    def __init__(self, cache_id):
        self.cache_id = cache_id

    def __str__(self):
        return "Unknown cache ID: " + self.cache_id
