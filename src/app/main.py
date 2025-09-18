from fastapi import FastAPI

from .routers import jobs
from .routers import molecules
from .routers import stats

app = FastAPI()

app.include_router(molecules.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")


@app.get("/health")
def health_check():
  return {"status": "ok"}
