from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from rq.exceptions import NoSuchJobError
from rq.job import Job

from ..dependencies import get_redis_queue

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, queue=Depends(get_redis_queue)):
  """
  Get the status and result of a background job.
  """
  try:
    job = Job.fetch(job_id, connection=queue.connection)
  except NoSuchJobError:
    raise HTTPException(status_code=404, detail="Job not found")

  response = {
    "job_id": job.id,
    "status": job.get_status(),
    "progress": job.meta.get("progress", 0),
    "result": job.return_value(),
  }
  return response
