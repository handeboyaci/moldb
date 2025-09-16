import redis

from src.app.config import settings

_redis_client = None


def get_redis_client():
  global _redis_client
  if _redis_client is None:
    _redis_client = redis.from_url(settings.REDIS_URL)
  return _redis_client
