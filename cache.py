from cachetools import TTLCache

# Create a cache with a maximum size of 100 items and TTL of 5 minutes
cache = TTLCache(maxsize=100, ttl=300) 