from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = (
        "MIRA Medical Document Assistant"
    )

    app_version: str = "0.2.0"
    environment: str = "development"

    llm_provider: str = "ollama"

    ollama_base_url: str = (
        "http://host.docker.internal:11434"
    )

    llm_model_name: str = "llama3.2"
    retrieval_top_k: int = 3

    chunk_size: int = 500
    chunk_overlap: int = 100

    # Required from .env. No password is stored in source code.
    database_url: str

    embedding_model_name: str = (
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )

    tavily_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()