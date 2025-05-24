from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)  # Cache for 5 minutes 