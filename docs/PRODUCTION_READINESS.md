# OncoPilot-AI v2.0 — Production Readiness Across 9 Dimensions

Target operating profile: ~50 daily active users, research/clinical decision-support use, workspace-isolated corpora, and heterogeneous document ingestion including text PDF, scanned PDF clinical records, DOCX, and TXT.

## 1. Use Case & Requirements
- Intended users: authenticated researchers, clinicians, data stewards, and administrators.
- Intended use: evidence retrieval, oncology literature triage, biomarker/mechanism synthesis, and preparation for expert review.
- Not autonomous: diagnosis, prescribing, dosing, or treatment changes require qualified clinical review.
- Default answer policy: no authorized/reliable evidence -> abstain rather than fabricate.
- Capacity baseline: ~50 DAU; start with a small stateless API service and scale only from measured concurrency/latency.

## 2. Data & Knowledge
- Supported: `.pdf`, `.docx`, `.txt`.
- PDF pipeline: native text extraction first; low-text pages fall back to OCR with Tesseract.
- Each source receives SHA-256 provenance, parser/OCR metadata, workspace ID, sensitivity label, ACLs, and ingestion timestamp.
- Duplicate source files are suppressed by source hash.
- Failed files appear in the index manifest and must be reviewed.
- Raw clinical files and generated indexes must live on encrypted storage with backup/retention controls owned by the deployment environment.

## 3. Architecture & Orchestration
- LangGraph flow: Coordinator -> Literature Retrieval -> Safety -> Trust -> Biomarker -> Translation -> Synthesis.
- Retrieval indexes are physically namespaced by workspace.
- Document ACLs are checked before retrieved content is passed to downstream agents.
- Sensitive evidence (`phi`/`restricted`) is not sent to an external LLM unless explicitly enabled by deployment policy.

## 4. Evaluation & Correctness
Release gates should include:
- Retrieval: Recall@K, Precision@K, MRR/nDCG on curated oncology questions.
- Generation: groundedness, citation fidelity, completeness, abstention accuracy, and contradiction rate.
- Safety: prompt-injection suite, unauthorized-document tests, PHI boundary tests, no-answer/adversarial cases.
- Regression: every production incident or expert-corrected failure becomes a new evaluation case.
Suggested initial release targets are project-specific and must be validated with representative data rather than treated as universal clinical thresholds.

## 5. Safety, Security & Governance
- Production must set `AUTH_MODE=jwt` and verify issuer/audience/JWKS from the enterprise IdP.
- Authorization boundary: workspace isolation + document role/user ACLs.
- Default deny for external LLM transmission of `phi`/`restricted` source passages.
- Prompt-injection indicators cause suspicious chunks to be excluded.
- Traces store question hashes rather than raw questions by default.
- Secrets are excluded from the repository and must come from a secret manager.
- Apply TLS, encryption at rest, least privilege, key rotation, audit retention, DLP/PHI procedures, and applicable organizational/legal requirements at the deployment layer.

## 6. Reliability & Resilience
- Workspace index readiness is exposed through `/ready`.
- Failed/unsupported documents do not silently enter the index; they are listed in the manifest.
- Index rebuild invalidates local retrieval caches.
- For production, place model calls behind explicit timeouts/retries and deploy behind a health-aware load balancer.
- Back up source metadata/index manifests and test restore procedures.

## 7. Performance & Cost
For ~50 DAU:
- Avoid premature distributed infrastructure; start with one small API service plus workspace-scoped FAISS indexes.
- Bound `top_k`, question length, upload size, and per-minute requests.
- Use retrieval before generation and keep only a small number of high-value chunks in context.
- Monitor p50/p95 latency, tokens/query, model spend/query, cache effectiveness, OCR time, and index size.
- Move rate limiting/cache state to a shared store only when multiple replicas make it necessary.

## 8. Deployment & Operations
- Container runs as a non-root user.
- CI runs unit/security-boundary tests on push/PR.
- Recommended promotion: dev -> staging -> canary -> production, with evaluation gates before promotion.
- Production configuration must use platform secret management, explicit CORS origins, JWT auth, encrypted persistent volumes/object storage, and centralized logs/metrics.

## 9. Observability & Continuous Improvement
- Every request receives a request ID and LangGraph trace ID.
- Agent events capture status/latency without source text.
- Monitor: request volume, error/timeout rate, p95 latency, retrieval empty-rate, abstention rate, trust distribution, safety flags, external-LLM usage, OCR failures, and authorization denials.
- User/expert corrections should feed a curated failure set and regression evaluation.

## Production go-live checklist
1. `APP_ENV=production`, `AUTH_MODE=jwt`, valid IdP settings.
2. No real secrets in git history; rotate any secret ever committed or shared.
3. Encrypted source/index storage and documented retention/deletion policy.
4. Verify workspace and document-level access tests.
5. Verify sensitive data cannot reach an external LLM unless policy explicitly permits it.
6. Run golden-set, adversarial, no-answer, and citation-fidelity evaluations.
7. Load test representative concurrent traffic and scanned-PDF OCR workload.
8. Configure central logs/metrics/alerts and incident ownership.
9. Test backup/restore and rollback.
