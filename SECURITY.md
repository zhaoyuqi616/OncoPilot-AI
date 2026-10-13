# Security policy and clinical-data boundary

OncoPilot-AI v2.0 is a production-oriented reference implementation, not a certification of HIPAA or other regulatory compliance. Compliance depends on the deployment, contracts, organizational controls, audit processes, and the actual data/use case.

- Never commit API keys, JWT secrets, patient records, or generated PHI traces.
- Production authentication must use the organization's IdP and `AUTH_MODE=jwt`.
- Use encrypted transport and encrypted persistent storage.
- Keep clinical workspaces isolated and assign document ACLs at ingestion.
- `phi` and `restricted` documents are blocked from external LLM transmission by default.
- If an external model provider is approved for protected data, enable it only after appropriate security/legal review and contractual controls.
- Rotate any credential that was ever committed, uploaded, or shared outside the intended secret manager.
