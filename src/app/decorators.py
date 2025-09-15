from functools import wraps
from unittest.mock import patch

from fastapi import status
from fastapi.responses import JSONResponse

from .dependencies import task_queue


def asynchronous_task(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    task_to_enqueue, *task_args = func(*args, **kwargs)

    if not task_queue.is_async:
      db_session = kwargs.get("db")

      def override_get_db():
        yield db_session

      with patch("src.app.dependencies.get_db", new=override_get_db):
        job = task_queue.enqueue(task_to_enqueue, *task_args)
    else:
      job = task_queue.enqueue(task_to_enqueue, *task_args)

    return JSONResponse(
      status_code=status.HTTP_202_ACCEPTED,
      content={"job_id": job.id, "status": job.get_status()},
    )

  return wrapper
