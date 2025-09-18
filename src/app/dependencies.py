import contextvars

import redis
from rq import Queue

from .config import settings
from .database import get_session_local

redis_conn = redis.from_url(settings.REDIS_URL)

task_queue = Queue(is_async=True, connection=redis_conn)

db_session_context = contextvars.ContextVar("db_session", default=None)


def get_db(db_url: str | None = None):
  # if a session is already provided via context, use it
  if (override_session := db_session_context.get()) is not None:
    yield override_session
    return

  # otherwise, create a new one
  session_local = get_session_local(db_url if db_url else settings.DATABASE_URL)
  db = session_local()
  try:
    yield db
  finally:
    db.close()


def get_redis_queue():
  yield task_queue
