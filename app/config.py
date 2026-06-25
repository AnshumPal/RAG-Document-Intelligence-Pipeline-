from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    chunk_size: int = 512
    chunk_overlap: int = 64

    database_url: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb"


settings = Settings()
