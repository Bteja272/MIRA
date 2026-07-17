from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MIRA"
    app_version: str = "0.2.0"
    environment: str = "development"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://host.docker.internal:11434"
    llm_model_name: str = "llama3.2"
    retrieval_top_k: int = 3  

    chunk_size: int = 500
    chunk_overlap: int = 100

    database_url: str = "postgresql://postgres:Postgres@localhost:5434/mira_db"

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    tavily_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()