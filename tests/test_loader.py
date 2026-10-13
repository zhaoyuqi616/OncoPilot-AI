from pathlib import Path

from oncopilot_ai.ingestion.loader import load_document


def test_txt_loader_adds_provenance(tmp_path: Path):
    p = tmp_path / "example.txt"
    p.write_text("EGFR resistance evidence", encoding="utf-8")
    docs = load_document(p, "w1", {"sensitivity": "internal", "allowed_roles": ["researcher"]})
    assert docs[0]["workspace_id"] == "w1"
    assert docs[0]["sensitivity"] == "internal"
    assert docs[0]["source_sha256"]
    assert docs[0]["allowed_roles"] == ["researcher"]
