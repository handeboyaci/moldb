from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from .. import dependencies
from ..services.job_service import JobService
from ..services.molecule_service import MoleculeService

router = APIRouter()


@router.get("/stats/molecules/count", tags=["stats"])
def get_molecule_count(db: Session = Depends(dependencies.get_db)):
  """
  Get the total number of molecules in the database.
  """
  service = MoleculeService(db)
  return {"count": service.get_molecule_count()}


@router.get("/stats/jobs/active", tags=["stats"])
def get_active_jobs():
  """
  Get a list of currently active jobs.
  """
  service = JobService()
  return service.get_active_jobs()
