from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
	"""Application configuration loaded from environment or .env file.

	Designed to be imported across modules via `get_settings()`.
	"""
	# LLM/Observability
	openai_api_key: str | None = None
	langchain_tracing_v2: bool = False
	langchain_api_key: str | None = None
	langchain_project: str | None = "banking-ops"
	google_api_key: str | None = None

	# Datastores
	mongodb_uri: str = "mongodb://localhost:27017"
	mongodb_db: str = "banking_ops"
	redis_url: str = "redis://localhost:6379/0"

	# Vector store
	vector_db_path: str = "./data/vectorstore"

	# App
	allow_debug: bool = False

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
	return AppSettings()


