from __future__ import annotations

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

    app_version: str = "0.3.0"
    environment: str = "development"

    # LLM provider configuration.
    llm_provider: str = "ollama"
    llm_fallback_provider: str = ""

    # Existing setting retained for backward compatibility.
    llm_model_name: str = "llama3.2"

    # Ollama.
    ollama_base_url: str = (
        "http://host.docker.internal:11434"
    )

    # If omitted, LLM_MODEL_NAME is used.
    ollama_model_name: str = ""

    # Groq.
    groq_api_key: SecretStr | None = None

    groq_base_url: str = (
        "https://api.groq.com/openai/v1"
    )

    groq_model_name: str = (
        "openai/gpt-oss-20b"
    )

    # Retrieval.
    retrieval_top_k: int = 3
    retrieval_candidate_k: int = 10
    retrieval_rrf_k: int = 60

    retrieval_semantic_weight: float = 1.0
    retrieval_lexical_weight: float = 1.0

    retrieval_bm25_k1: float = 1.5
    retrieval_bm25_b: float = 0.75

    # Second-stage cross-encoder reranking.
    retrieval_reranker_enabled: bool = True
    retrieval_reranker_model_name: str = (
        "cross-encoder/"
        "ms-marco-MiniLM-L6-v2"
    )
    retrieval_reranker_batch_size: int = 16

    # Empty means SentenceTransformers chooses the device.
    retrieval_reranker_device: str = ""

    # Reranking improves ranking quality but is not required
    # for availability. When enabled, fall back to fused RRF
    # ranking if model loading or inference fails.
    retrieval_reranker_fail_open: bool = True

    # Protects unscoped lexical search from loading an
    # unbounded number of chunks into application memory.
    retrieval_lexical_max_chunks: int = 2000

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

    @property
    def resolved_ollama_model_name(
        self,
    ) -> str:
        explicit_model = (
            self
            .ollama_model_name
            .strip()
        )

        if explicit_model:
            return explicit_model

        return (
            self
            .llm_model_name
            .strip()
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
                "cors_allowed_origins must be "
                "a list or comma-separated string."
            )

        normalized: list[str] = []

        for origin in value:
            cleaned = (
                str(origin)
                .strip()
                .rstrip("/")
            )

            if (
                cleaned
                and cleaned not in normalized
            ):
                normalized.append(
                    cleaned
                )

        return normalized

    @field_validator(
        "llm_provider",
        "llm_fallback_provider",
        mode="before",
    )
    @classmethod
    def normalize_provider_name(
        cls,
        value,
    ):
        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .lower()
        )

    @model_validator(mode="after")
    def validate_runtime_settings(self):
        supported_providers = {
            "groq",
            "ollama",
        }

        if (
            self.llm_provider
            not in supported_providers
        ):
            raise ValueError(
                "llm_provider must be one of: "
                "groq, ollama."
            )

        if (
            self.llm_fallback_provider
            and self.llm_fallback_provider
            not in supported_providers
        ):
            raise ValueError(
                "llm_fallback_provider must be "
                "empty or one of: groq, ollama."
            )

        if (
            self.llm_fallback_provider
            == self.llm_provider
        ):
            raise ValueError(
                "llm_fallback_provider must "
                "differ from llm_provider."
            )

        if not (
            self.resolved_ollama_model_name
        ):
            raise ValueError(
                "An Ollama model name is required."
            )

        if not self.groq_model_name.strip():
            raise ValueError(
                "groq_model_name is required."
            )

        if self.chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater "
                "than zero."
            )

        if self.chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if (
            self.chunk_overlap
            >= self.chunk_size
        ):
            raise ValueError(
                "chunk_overlap must be smaller "
                "than chunk_size."
            )

        positive_integer_fields = {
            "retrieval_top_k": (
                self.retrieval_top_k
            ),
            "retrieval_candidate_k": (
                self.retrieval_candidate_k
            ),
            "retrieval_rrf_k": (
                self.retrieval_rrf_k
            ),
            "retrieval_lexical_max_chunks": (
                self.retrieval_lexical_max_chunks
            ),
            "retrieval_reranker_batch_size": (
                self.retrieval_reranker_batch_size
            ),
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

        for (
            field_name,
            value,
        ) in positive_integer_fields.items():
            if value <= 0:
                raise ValueError(
                    f"{field_name} must be "
                    "greater than zero."
                )

        if (
            self.retrieval_candidate_k
            < self.retrieval_top_k
        ):
            raise ValueError(
                "retrieval_candidate_k must be "
                "greater than or equal to "
                "retrieval_top_k."
            )

        if (
            self.retrieval_semantic_weight
            < 0
            or self.retrieval_lexical_weight
            < 0
        ):
            raise ValueError(
                "Retrieval fusion weights "
                "cannot be negative."
            )

        if (
            self.retrieval_semantic_weight
            == 0
            and self.retrieval_lexical_weight
            == 0
        ):
            raise ValueError(
                "At least one retrieval fusion "
                "weight must be greater than zero."
            )

        if (
            self.retrieval_reranker_enabled
            and not self
            .retrieval_reranker_model_name
            .strip()
        ):
            raise ValueError(
                "retrieval_reranker_model_name "
                "is required when reranking "
                "is enabled."
            )

        if self.retrieval_bm25_k1 <= 0:
            raise ValueError(
                "retrieval_bm25_k1 must be "
                "greater than zero."
            )

        if not (
            0.0
            <= self.retrieval_bm25_b
            <= 1.0
        ):
            raise ValueError(
                "retrieval_bm25_b must be "
                "between 0 and 1."
            )

        if (
            self.cors_allow_credentials
            and "*"
            in self.cors_allowed_origins
        ):
            raise ValueError(
                "Wildcard CORS origins cannot "
                "be used when credentials are enabled."
            )

        return self


settings = Settings()