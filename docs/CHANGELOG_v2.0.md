# What is new in OncoPilot-AI v2.0

## Security and data boundaries
- Added workspace-scoped FAISS indexes instead of one global index.
- Added authenticated `AuthContext` and JWT/OIDC-compatible validation using JWKS.
- Added document `allowed_roles` / `allowed_users` ACL checks before content reaches agents or LLMs.
- Added sensitivity labels (`public`, `internal`, `phi`, `restricted`).
- Added default-deny external LLM policy for `phi` and `restricted` evidence.
- Added prompt-injection screening for ingested/retrieved content.
- Restricted `/graph` to admins and `/trace/{id}` to the matching workspace.
- Replaced raw-question trace storage with hashes by default.
- Removed committed `.env`; sanitized `.env.example`; added `.gitignore`.

## Ingestion
- Replaced TXT-only ingestion with PDF/DOCX/TXT ingestion.
- Added native PDF extraction + OCR fallback for scanned clinical-record pages.
- Added provenance: SHA-256, parser, page/section, OCR flag, ingestion time, workspace, sensitivity, ACLs.
- Added deduplication by source hash and an index manifest with ingestion errors.

## Agent workflow
- Added a Safety Agent between retrieval and trust scoring.
- Hardened synthesis prompt so source documents are treated as untrusted data, not instructions.
- Added patient-specific/high-stakes query flags and human-review safety messaging.
- Defaulted to stronger abstention behavior (`include_low_confidence=false`, higher default trust threshold).

## Reliability / operations
- Added `/ready` checks for workspace index, production authentication, CORS, and trace redaction.
- Added request IDs, basic rate limiting, security headers, response timing, and bounded request parameters.
- Index rebuild now clears retrieval caches.

## Deployment / quality
- Added non-root Docker image with OCR runtime.
- Added GitHub Actions CI.
- Added production-readiness documentation and a 9-dimension go-live checklist.
- Expanded unit tests for ACLs, safety, redacted traces, and multi-format ingestion.

## Capacity posture for ~50 DAU
- Keeps infrastructure intentionally simple: a small stateless API tier plus workspace-scoped local vector indexes is adequate as a starting architecture.
- Adds limits and monitoring hooks first; distributed vector DB, Redis, or autoscaling should be introduced only when measured load/availability requirements justify them.
