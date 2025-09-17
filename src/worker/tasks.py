import json
import os
from itertools import islice
from pathlib import Path

import rq
from rq.decorators import job
from rq.job import Job

from src.app import dependencies
from src.app.config import settings
from src.app.dependencies import redis_conn
from src.app.services.molecule_service import MoleculeService


@job("default", connection=redis_conn)
def ingest_file_job(file_path: str):
  return _ingest_file_job(file_path)


def _ingest_file_job(file_path: str):
  """Meta-job to read a file and create chunk-processing jobs."""
  job = rq.get_current_job()
  if job:
    job.meta["progress"] = 0
    job.save_meta()

  # Security: Ensure the file path is within the /uploads directory
  uploads_dir = "/uploads"
  full_path_str = os.path.abspath(os.path.join(uploads_dir, file_path))
  if not full_path_str.startswith(os.path.abspath(uploads_dir)):
    raise ValueError("File path is outside of the allowed directory")

  full_path = Path(full_path_str)

  try:
    total_size = full_path.stat().st_size
    if job:
      job.meta["total_records"] = "Calculating..."
      job.save_meta()
    chunk_jobs = []
    with open(full_path, "r") as f:
      chunk_size = settings.INGESTION_CHUNK_SIZE
      chunk_num = 0
      while True:
        chunk = list(islice(f, chunk_size))
        if not chunk:
          break
        if job:
            chunk_job = process_chunk_job.delay(chunk, chunk_num * chunk_size, meta={"parent_job_id": job.id})
        else:
            chunk_job = _process_chunk_job(chunk, chunk_num * chunk_size)
        chunk_jobs.append(chunk_job)
        chunk_num += 1
        if chunk_num % 5 == 0:
          if job:
            progress = (f.tell() / total_size) * 100 if total_size > 0 else 100
            job.meta["progress"] = progress
            job.save_meta()

    if job:
        aggregate_results_job.delay(job.id, depends_on=chunk_jobs)
        job.meta["progress"] = 100
        job.save_meta()
    else:
        # Sync case
        return _aggregate_results_job(None, chunk_jobs)

  except FileNotFoundError:
    job.meta["status"] = "Error: File not found"
    job.save_meta()
    raise
  except Exception as e:
    job.meta["status"] = f"Error: {e}"
    job.save_meta()
    raise


@job("default", connection=redis_conn)
def process_chunk_job(smiles_list: list[str], starting_line: int):
  return _process_chunk_job(smiles_list, starting_line)


def _process_chunk_job(smiles_list: list[str], starting_line: int):
  """Worker job to process a chunk of SMILES strings."""
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  results = service.create_molecules_from_smiles(smiles_list, starting_line)
  job = rq.get_current_job()
  if job:
    redis_conn.hset(f"job:{job.meta['parent_job_id']}:results", job.id, json.dumps(results))
  return results


@job("default", connection=redis_conn)
def aggregate_results_job(parent_job_id: str):
  return _aggregate_results_job(parent_job_id)


def _aggregate_results_job(parent_job_id: str, sync_results: list = None):
  """Aggregates results from all chunk jobs."""
  job = rq.get_current_job()
  if job:
    job.meta["progress"] = 0
    job.save_meta()

  if sync_results:
      results = sync_results
  else:
      results_hash = redis_conn.hgetall(f"job:{parent_job_id}:results")
      results = [json.loads(r) for r in results_hash.values()]

  total_ingested = 0
  total_failed = 0
  all_errors = []

  for i, result in enumerate(results):
    total_ingested += result["successfully_ingested"]
    total_failed += result["failed_count"]
    all_errors.extend(result["errors"])
    if job:
      job.meta["progress"] = (i + 1) / len(results) * 100
      job.save_meta()

  final_result = {
    "total_records_processed": total_ingested + total_failed,
    "successfully_ingested": total_ingested,
    "failed_count": total_failed,
    "errors": all_errors,
  }

  if parent_job_id:
    # Save final result to parent job
    parent_job = Job.fetch(parent_job_id, connection=redis_conn)
    parent_job.result = final_result
    parent_job.save()

    # Clean up Redis hash
    redis_conn.delete(f"job:{parent_job_id}:results")

  return final_result


def create_molecule_task(smiles: str):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.create_molecule(smiles)


def search_molecules_task(search_params: dict):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.search_molecules(**search_params)


def find_similar_molecules_task(smiles: str, min_similarity: float, force_recompute: bool = False):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.find_similar_molecules(smiles, min_similarity, force_recompute)


def substructure_search_task(smiles: str):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.substructure_search(smiles)
