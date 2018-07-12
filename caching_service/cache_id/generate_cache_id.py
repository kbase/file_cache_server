"""
Generate a cache ID from a service token and JSON.
"""
import json
from caching_service.hash import bhash


# Validate the JSON
def generate_cache_id(token, json_data):
    """
    Generate a cache ID from a service token and serializable data
    Args:
        token - required - Pass in a service authentication token
        params - required - Pass in an arbitrary non-empty string of identify cache data
    Returns a cache ID (a blake2b hash)
    """
    if not token or not isinstance(token, str):
        raise TypeError('`token` must be a non-empty string')
    # Get a uniform json string with keys sorted and whitespace removed
    if not json_data:
        raise TypeError('Must provide non-empty json_data for the cache identifier')
    json_text = json.dumps(json_data, sort_keys=True)
    concatenated = token + '\n' + json_text
    return bhash(concatenated)
