"""
Generate a cache ID from a service token and JSON.
"""
import json
from caching_service.hash import bhash


# Validate the JSON
def generate_cache_id(token_id, json_data):
    """
    Generate a cache ID from a service token and serializable data
    Args:
        token_id - required - Pass in a service authentication token data in the form of
          'auth_url:user:name'
        params - required - Pass in an arbitrary non-empty string of identify cache data
    Returns a cache ID (a blake2b hash)
    """
    if not token_id or not isinstance(token_id, str):
        raise TypeError('`token_id` must be a non-empty string')
    # Get a uniform json string with keys sorted and whitespace removed
    if not json_data or not isinstance(json_data, dict):
        raise TypeError('Must provide non-empty JSON data for the cache identifier')
    json_text = json.dumps(json_data, sort_keys=True)
    concatenated = token_id + '\n' + json_text
    return bhash(concatenated)
