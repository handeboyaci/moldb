import redis
from rq import Queue

from .config import settings
from .database import SessionLocal

redis_conn = redis.from_url(settings.REDIS_URL)

# Create a queue that is either async or sync based on the TESTING flag
task_queue = Queue(is_async=not settings.TESTING, connection=redis_conn)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
