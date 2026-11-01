# Safety and Privacy

## Medical safety

1. MediExplain AI is **informational and educational**, not a diagnostic system.
2. It never recommends medicines, dosages or treatments.
3. Every flagged value shows the **original laboratory reference range**.
4. An out-of-range result is explicitly distinguished from a disease diagnosis.
5. Critical-value flags use a configurable rule table and escalate to clear urgent-care guidance — never to AI reassurance.
6. The deterministic analyzer decides LOW/HIGH/NORMAL. The LLM may only explain, never re-classify or invent values.
7. If a reference range is missing, status is `UNKNOWN` — the system does not substitute a generic range.
8. If a numeric value cannot be parsed reliably, status is `NEEDS_REVIEW` instead of guessing.
9. AI explanations carry a visible "AI-generated, unverified" label.
10. Users are encouraged to consult a qualified healthcare professional.

### Critical-value thresholds

`backend/services/critical_values.py` contains **placeholder thresholds** (e.g. haemoglobin, platelets, glucose, potassium). These are engineering placeholders for demonstration and **must be reviewed and validated by a clinician** before any real-world use. Do not present them as clinically approved.

### LLM guardrails

The system prompt (`backend/services/ai/prompts.py`) enforces:

- Use only supplied report data and retrieved references.
- Never invent missing test values.
- Never diagnose or prescribe.
- State uncertainty; decline when information is insufficient.
- Cite retrieved sources when RAG is enabled.
- Answer in the user's selected language.

The service validates that no numeric value from the report is altered in the returned text where it can be checked; the canonical values shown in the UI always come from the database, not the LLM.

## Privacy and security

### Implemented (MVP)

- bcrypt password hashing.
- JWT bearer authentication.
- Per-user authorization on every report route; cross-user access returns 404.
- Upload validation: extension allow-list, file-signature check, size limit, page limit.
- Filenames replaced with server-generated UUIDs; original name stored only as metadata.
- Uploads stored outside any static web root.
- Duplicate detection per user via SHA-256 hash.
- No report contents written to application logs.
- Configurable secrets via environment variables; `.env` is git-ignored.

### Required before any real deployment

- HTTPS everywhere; HSTS.
- Encryption at rest for uploads and database.
- Database backups with retention policy.
- Rate limiting and account lockout.
- Audit logging of access/export/delete actions.
- Data-deletion and retention controls exposed in the UI.
- Malware scanning of uploads.
- Secret management (vault/KMS) instead of `.env`.
- DPDP Act review (India) and applicable medical-software regulation.
- Formal clinical review of all reference material, thresholds and escalation text.

## Data minimisation

Collect only: name, email, password hash. Do not request age/sex unless required for range contextualisation, and never store identifiers that are not needed. Sample reports used in development must be synthetic or properly de-identified.
