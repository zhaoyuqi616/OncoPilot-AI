from __future__ import annotations

from pathlib import Path

from oncopilot_ai.config import settings


def load_txt_documents_from_folder(folder_path: str | None = None) -> list[dict[str, str]]:
    folder = Path(folder_path or settings.data_dir)
    documents: list[dict[str, str]] = []
    for path in sorted(folder.glob("*.txt")):
        documents.append(
            {
                "doc_id": path.stem.upper(),
                "title": path.stem.replace("_", " ").title(),
                "text": path.read_text(encoding="utf-8"),
            }
        )
    return documents
