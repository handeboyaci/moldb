from functools import wraps

from fastapi import status
from fastapi.responses import JSONResponse

from .dependencies import db_session_context
from .dependencies import task_queue


def asynchronous_task(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    sync = kwargs.get("sync", False)
    task_to_enqueue, *task_args = func(*args, **kwargs)

    if sync:
      db_session = kwargs.get("db")
      token = db_session_context.set(db_session)
      try:
        return task_to_enqueue(*task_args)
      finally:
        db_session_context.reset(token)

    job = task_queue.enqueue(task_to_enqueue, *task_args)

    return JSONResponse(
      status_code=status.HTTP_202_ACCEPTED,
      content={"job_id": job.id, "status": job.get_status()},
    )

  return wrapper
