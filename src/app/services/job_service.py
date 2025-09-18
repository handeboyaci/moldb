from rq import Queue
from rq.job import Job

from ..dependencies import redis_conn


class JobService:
  def __init__(self):
    self.queue = Queue("default", connection=redis_conn)

  def get_active_jobs(self) -> list[dict]:
    job_ids = (
      self.queue.started_job_registry.get_job_ids()
      + self.queue.scheduled_job_registry.get_job_ids()
    )

    if not job_ids:
      return []
    jobs = Job.fetch_many(job_ids, connection=redis_conn)
    return [
      {
        "job_id": job.id,
        "status": job.get_status(refresh=True),
        "description": job.description,
        "started_at": job.started_at,
        "meta": job.meta,
      }
      for job in jobs
      if job is not None
    ]
