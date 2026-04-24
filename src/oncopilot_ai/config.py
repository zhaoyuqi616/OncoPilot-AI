from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.2"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_top_k: int = 4
    data_dir: str = "data/sample_docs"
    faiss_index_path: str = "artifacts/faiss/oncology.index"
    metadata_path: str = "artifacts/metadata/chunks.json"
    trace_dir: str = "artifacts/traces"
    chunk_size_words: int = 120
    chunk_overlap_words: int = 30


settings = Settings()
