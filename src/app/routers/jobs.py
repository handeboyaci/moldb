from fastapi import APIRouter, HTTPException, status
from rq.job import Job

from src.app.dependencies import redis_conn

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
  try:
    job = Job.fetch(job_id, connection=redis_conn)
  except Exception:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

  response = {
    "job_id": job.id,
    "status": job.get_status(),
    "result": job.return_value() if job.is_finished else None,
    "error": job.exc_info if job.is_failed else None,
  }
  return response
