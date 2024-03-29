import os
import sad_libraries.redis as sad_redis
import logging
import json
import requests
from urllib.parse import quote

logger = logging.getLogger("tmdb_lib")
logger.setLevel(os.environ.get("TMDB_LIB_LOG_LEVEL", "INFO"))
logger.handlers = []
console_handler = logging.StreamHandler()
console_handler.setLevel(os.environ.get("TMDB_LIB_LOG_LEVEL", "INFO"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def search_movie_by_query_and_year(*, query: str, year: int):
    return search(filters=[{"query": query, "year": year}], type="movie")


def search_tv_by_title(*, title: str):
    return search(filters=[{"query": title}], type="tv")


def get_config():
    api_access_token = os.getenv("TMDB_API_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }
    url = "https://api.themoviedb.org/3/configuration"
    cached = sad_redis.get_from_cache(key=url)
    if cached:
        logger.debug("TMDB Cache hit for /configuration)")
        return cached
    logger.debug("TMDB Cache miss for /configuration, requesting from TMDB")
    r = requests.get(url, headers=headers)
    r.raise_for_status()  # Raises an exception if not a 200 response code
    response_json = json.loads(r.text)
    logger.debug(f"Response code: {r.status_code}")
    logger.debug(f"Response json: {response_json}")
    sad_redis.save_to_cache(key=url, data=response_json, ttl=604800)
    return response_json


def search(*, filters: [dict], type: str):
    api_access_token = os.getenv("TMDB_API_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }
    query_string = encode_querystring(filters)
    url = f"https://api.themoviedb.org/3/search/{type}?include_adult=false&language=en-US&{query_string}"
    cached = sad_redis.get_from_cache(key=url)
    if cached:
        logger.debug(f"TMDB Cache hit for {url}), response: {cached}")
        return cached
    logger.debug(f"TMDB Cache miss for {url}), requesting from TMDB")
    r = requests.get(url, headers=headers)
    r.raise_for_status()  # Raises an exception if not a 200 response code
    response_json = json.loads(r.text)
    sad_redis.save_to_cache(key=url, data=response_json, ttl=28800)
    logger.debug(f"TMDB response for {url}, response {response_json}")
    return response_json


def encode_querystring(data):
    encoded_params = []
    for item in data:
        for key, value in item.items():
            encoded_key = quote(str(key))
            encoded_value = quote(str(value))
            encoded_params.append(f"{encoded_key}={encoded_value}")
    return '&'.join(encoded_params)
