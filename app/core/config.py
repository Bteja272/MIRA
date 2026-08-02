from pydantic import (
    SecretStr,
    field_validator,
    model_validator,
)
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

    database_url: str
    sql_echo: bool = False

    embedding_model_name: str = (
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )

    # Frontend/API settings.
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    cors_allow_credentials: bool = True

    # Structured medical extraction settings.
    extraction_max_context_characters: int = 16_000
    extraction_llm_timeout_seconds: int = 180
    extraction_llm_max_output_tokens: int = 1_600
    extraction_llm_context_window: int = 8_192
    extraction_llm_keep_alive: str = "10m"
    extraction_enable_repair: bool = True
    extraction_max_repair_prompt_characters: int = 12_000
    extraction_allow_deterministic_fallback: bool = True
    extraction_log_timings: bool = True

    tavily_api_key: str = ""

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator(
        "cors_allowed_origins",
        mode="before",
    )
    @classmethod
    def normalize_cors_origins(
        cls,
        value,
    ):
        if isinstance(value, str):
            value = [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        if not isinstance(value, list):
            raise ValueError(
                "cors_allowed_origins must be a list "
                "or comma-separated string."
            )

        normalized: list[str] = []

        for origin in value:
            cleaned = str(origin).strip().rstrip("/")

            if (
                cleaned
                and cleaned not in normalized
            ):
                normalized.append(cleaned)

        return normalized

    @model_validator(mode="after")
    def validate_runtime_settings(self):
        if self.chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if self.chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        positive_integer_fields = {
            "retrieval_top_k": self.retrieval_top_k,
            "extraction_max_context_characters": (
                self.extraction_max_context_characters
            ),
            "extraction_llm_timeout_seconds": (
                self.extraction_llm_timeout_seconds
            ),
            "extraction_llm_max_output_tokens": (
                self.extraction_llm_max_output_tokens
            ),
            "extraction_llm_context_window": (
                self.extraction_llm_context_window
            ),
            "extraction_max_repair_prompt_characters": (
                self.extraction_max_repair_prompt_characters
            ),
            "access_token_expire_minutes": (
                self.access_token_expire_minutes
            ),
        }

        for field_name, value in positive_integer_fields.items():
            if value <= 0:
                raise ValueError(
                    f"{field_name} must be greater than zero."
                )

        if (
            self.cors_allow_credentials
            and "*" in self.cors_allowed_origins
        ):
            raise ValueError(
                "Wildcard CORS origins cannot be used "
                "when credentials are enabled."
            )

        return self


settings = Settings()