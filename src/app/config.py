from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
  DATABASE_URL: str = ""
  REDIS_URL: str = ""

  TESTING: bool = False
  INGESTION_CHUNK_SIZE: int = 10000

  model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
