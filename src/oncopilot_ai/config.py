from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration. Secrets must be injected by the deployment platform."""

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    app_env: str = "development"  # development | staging | production
    app_version: str = "2.0.0"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.2"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Capacity / API controls (~50 DAU target)
    default_top_k: int = 6
    max_top_k: int = 12
    max_question_chars: int = 4000
    rate_limit_per_minute: int = 30
    max_upload_mb: int = 40
    request_timeout_seconds: int = 45

    # Workspace-scoped storage. Each workspace gets its own retrieval index.
    workspace_data_root: str = "data/workspaces"
    workspace_artifact_root: str = "artifacts/workspaces"
    trace_dir: str = "artifacts/traces"
    chunk_size_words: int = 180
    chunk_overlap_words: int = 40

    # Ingestion / OCR
    ocr_enabled: bool = True
    ocr_min_native_chars_per_page: int = 40
    ocr_min_confidence: float = 0.0  # reserved for OCR engines that expose confidence
    allowed_extensions: str = ".pdf,.docx,.txt"

    # Authentication and authorization
    auth_mode: str = "dev"  # dev | jwt
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_jwks_url: str | None = None

    # Data-boundary defaults
    allow_external_llm_for_sensitive: bool = False
    sensitive_labels: str = "phi,restricted"
    trace_store_question: bool = False
    trace_store_user_id: bool = False

    # CORS; production should list explicit trusted origins.
    allowed_origins: str = "http://localhost:7860,http://localhost:8000"

    @property
    def allowed_extension_set(self) -> set[str]:
        return {x.strip().lower() for x in self.allowed_extensions.split(",") if x.strip()}

    @property
    def sensitive_label_set(self) -> set[str]:
        return {x.strip().lower() for x in self.sensitive_labels.split(",") if x.strip()}

    @property
    def origin_list(self) -> list[str]:
        return [x.strip() for x in self.allowed_origins.split(",") if x.strip()]


settings = Settings()
