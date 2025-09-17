import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.worker.tasks import (
  _aggregate_results_job,
  _ingest_file_job,
  _process_chunk_job,
)


@pytest.fixture
def mock_rq_job():
  with patch("rq.get_current_job") as mock_get_job:
    mock_job = MagicMock()
    mock_job.meta = {}
    mock_get_job.return_value = mock_job
    yield mock_job


def test_ingest_file_job_success(mock_rq_job):
  """Test ingest_file_job successfully enqueues chunk jobs."""
  # Setup
  file_path = "test_smiles.txt"
  smiles_data = "CCO\nCCN\nCNC\n"

  with (
    patch("builtins.open", mock_open(read_data=smiles_data)),
    patch("src.worker.tasks.Path.stat") as mock_stat,
    patch("src.worker.tasks.process_chunk_job.delay") as mock_chunk_delay,
    patch("src.worker.tasks.aggregate_results_job.delay") as mock_aggregate_delay,
  ):
    mock_stat.return_value.st_size = 15
    # Execute
    _ingest_file_job(file_path)

    # Assert
    assert mock_chunk_delay.call_count == 1  # Based on chunk size
    mock_aggregate_delay.assert_called_once()
    mock_rq_job.save_meta.assert_called()


def test_ingest_file_job_file_not_found(mock_rq_job):
  """Test ingest_file_job raises ValueError for a file that doesn't exist."""
  with (
    patch("src.worker.tasks.Path.stat", side_effect=FileNotFoundError),
    pytest.raises(FileNotFoundError),
  ):
    _ingest_file_job("non_existent_file.txt")


def test_ingest_file_job_path_traversal(mock_rq_job):
  """Test ingest_file_job raises ValueError for a path traversal attempt."""
  with pytest.raises(ValueError, match="File path is outside of the allowed directory"):
    _ingest_file_job("../../etc/passwd")


@patch("src.worker.tasks.redis_conn")
@patch("src.app.dependencies.get_db")
@patch("src.worker.tasks.MoleculeService")
def test_process_chunk_job(MockMoleculeService, mock_get_db, mock_redis_conn):
  """Test process_chunk_job calls the service with the correct data."""
  # Setup
  mock_db_session = MagicMock()
  mock_get_db.return_value = iter([mock_db_session])
  mock_service_instance = MockMoleculeService.return_value
  mock_service_instance.create_molecules_from_smiles.return_value = {
    "successfully_ingested": 2,
    "failed_count": 0,
    "errors": [],
  }
  smiles_list = ["CCO", "CCN"]
  starting_line = 0

  with patch("rq.get_current_job") as mock_get_job:
    mock_job = MagicMock()
    mock_job.meta = {"parent_job_id": "parent_id"}
    mock_get_job.return_value = mock_job

    # Execute
    # Call the original function, bypassing the @job decorator
    _process_chunk_job(smiles_list, starting_line)

    # Assert
    mock_service_instance.create_molecules_from_smiles.assert_called_once_with(
      smiles_list, starting_line
    )
    mock_redis_conn.hset.assert_called_once()


@patch("rq.get_current_job")
@patch("src.worker.tasks.Job.fetch")
@patch("src.worker.tasks.redis_conn")
def test_aggregate_results_job(mock_redis_conn, mock_job_fetch, mock_get_current_job):
  """Test aggregate_results_job aggregates results correctly."""
  # Setup
  mock_job = MagicMock()
  mock_get_current_job.return_value = mock_job
  parent_job_id = "parent_job"
  mock_parent_job = MagicMock()
  mock_parent_job.meta = {}
  mock_job_fetch.return_value = mock_parent_job

  results_hash = {
    b"job1": json.dumps(
      {
        "successfully_ingested": 10,
        "failed_count": 1,
        "skipped_count": 0,
        "errors": ["error1"],
      }
    ),
    b"job2": json.dumps(
      {
        "successfully_ingested": 15,
        "failed_count": 2,
        "skipped_count": 5,
        "errors": ["error2", "error3"],
      }
    ),
  }
  mock_redis_conn.hgetall.return_value = results_hash

  # Execute
  _aggregate_results_job(parent_job_id)

  # Assert
  mock_redis_conn.hgetall.assert_called_once_with(f"job:{parent_job_id}:results")
  assert mock_parent_job.meta["result"]["successfully_ingested"] == 25
  assert mock_parent_job.meta["result"]["failed_count"] == 3
  assert len(mock_parent_job.meta["result"]["errors"]) == 3
  mock_parent_job.save_meta.assert_called_once()
  mock_redis_conn.delete.assert_called_once_with(f"job:{parent_job_id}:results")
