"""
Generate a cache ID from a service token and JSON.
"""
from caching_service.hash import bhash


# Validate the JSON
def generate_cache_id(token, params):
    """
    Generate a cache ID from a service token and data
    Args:
        token - required - Pass in a service authentication token
        params - required - Pass in an arbitrary non-empty string of identify cache data
    Returns a cache ID (a blake2b hash)
    """
    print('params', 'token', params, token)
    if not token or not isinstance(token, str):
        raise TypeError('`token` must be a non-empty string')
    if not params or not isinstance(params, str):
        raise TypeError('`params` must be a non-empty string')
    concatenated = token + '\n' + params
    return bhash(concatenated)
