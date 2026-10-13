# OncoPilot-AI v2.0 — Production-Oriented Multi-Agent Oncology RAG

OncoPilot-AI is a LangGraph-based evidence copilot for oncology literature and authorized clinical documents. v2.0 upgrades the original research prototype around nine production-readiness dimensions: requirements, data, architecture, evaluation, safety/security, reliability, performance/cost, deployment, and observability.

## v2.0 architecture

`User -> AuthN/AuthZ -> Coordinator -> Workspace Retrieval -> Safety -> Trust -> Biomarker -> Translation -> Synthesis -> Evidence + Citations`

Important boundary: indexes are separated by workspace; document ACLs are checked before evidence reaches downstream agents. Source passages labeled `phi` or `restricted` are not sent to an external LLM by default.

## Supported ingestion

- Text PDFs: native extraction with PyMuPDF.
- Scanned PDFs / clinical records: OCR fallback with Tesseract when a page has insufficient native text.
- Word `.docx`: paragraphs and tables.
- Plain `.txt`.

Each source carries provenance, SHA-256, workspace, sensitivity, ACLs, parser/OCR information, and ingestion time.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
```

Tesseract must be installed on the host for scanned-PDF OCR. The included Dockerfile installs it.

## Add documents and build an index

Place authorized files under:

```text
data/workspaces/research-team/incoming/
```

Then:

```bash
python run_ingest.py --workspace research-team --sensitivity internal --roles researcher,clinician
```

For protected clinical records, use `--sensitivity phi`. External LLM transmission is disabled for those records by default.

## Run API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In development mode, pass headers such as `X-User-ID`, `X-Workspace-ID`, and `X-Roles`. Production must use `APP_ENV=production` and `AUTH_MODE=jwt` with enterprise issuer/audience/JWKS configuration.

Useful endpoints:
- `GET /health`
- `GET /ready`
- `POST /ask`
- `GET /trace/{trace_id}`
- `GET /graph` (admin only)

## Production-readiness documentation

See `docs/PRODUCTION_READINESS.md` for the full 9-dimension checklist and `docs/CHANGELOG_v2.0.md` for the v1 -> v2 delta.

## Safety statement

This repository is a production-oriented engineering reference, not a medical device or compliance certification. Patient-specific diagnosis/treatment decisions require qualified clinical review and the deployment must satisfy the applicable organizational, security, privacy, and legal controls.
