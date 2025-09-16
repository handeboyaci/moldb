from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  DATABASE_URL: str
  REDIS_URL: str
  TESTING: bool = False
  INGESTION_CHUNK_SIZE: int = 10000

  class Config:
    env_file = ".env"


settings = Settings()
