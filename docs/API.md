# API Reference

Base URL: `http://localhost:8000`

All report endpoints require:

```http
Authorization: Bearer <access_token>
```

## Health

### `GET /api/health`

```json
{ "status": "ok", "app": "MediExplain AI", "version": "0.1.0", "ai_provider": "ollama" }
```

## Auth

### `POST /api/auth/register`

```json
{ "name": "Demo User", "email": "demo@example.com", "password": "demo12345" }
```

`201 Created`

```json
{ "id": 1, "name": "Demo User", "email": "demo@example.com", "created_at": "2026-11-02T10:00:00Z" }
```

### `POST /api/auth/login`

```json
{ "email": "demo@example.com", "password": "demo12345" }
```

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "Demo User", "email": "demo@example.com" }
}
```

### `GET /api/auth/me`

Returns the current user.

## Reports

### `POST /api/reports/upload`

`multipart/form-data`, field `file` (`.pdf`, `.jpg`, `.jpeg`, `.png`, max 15 MB).

`201 Created`

```json
{
  "id": 1,
  "original_filename": "sample_cbc_report.pdf",
  "report_type": "CBC",
  "status": "completed",
  "extraction_method": "text",
  "page_count": 1,
  "created_at": "2026-11-02T10:05:00Z",
  "results": [
    {
      "id": 1,
      "test_name": "Hemoglobin",
      "value": 11.2,
      "value_text": "11.2",
      "unit": "g/dL",
      "range_low": 13.0,
      "range_high": 17.0,
      "range_text": "13 - 17",
      "status": "LOW",
      "critical_flag": false,
      "confidence": 0.95,
      "source_page": 1
    }
  ],
  "disclaimer": "Informational only — not a diagnosis..."
}
```

Duplicate (same user, same bytes): `409 Conflict` with `{ "detail": { "message": "...", "report_id": 1 } }`.

### `GET /api/reports`

```json
{ "total": 2, "items": [ { "id": 2, "original_filename": "...", "status": "completed", "abnormal_count": 1, "result_count": 12, "created_at": "..." } ] }
```

### `GET /api/reports/{id}`

Full report with results and any stored explanations.

### `GET /api/reports/{id}/results`

```json
{
  "report_id": 1,
  "results": [ { "test_name": "Hemoglobin", "status": "LOW", "value": 11.2, "unit": "g/dL", "range_low": 13, "range_high": 17 } ]
}
```

### `POST /api/reports/{id}/analyze`

Re-runs the deterministic analyzer against the stored extraction and returns the updated results. Idempotent.

### `POST /api/reports/{id}/explain?language=en`

Languages: `en`, `hi`, `hinglish`.

```json
{
  "report_id": 1,
  "language": "en",
  "provider": "template",
  "explanations": [
    {
      "result_id": 1,
      "test_name": "Hemoglobin",
      "text": "Hemoglobin is the protein in red blood cells that carries oxygen...",
      "model": "template",
      "source": "template"
    }
  ],
  "disclaimer": "AI-generated educational content, not medical advice."
}
```

### `DELETE /api/reports/{id}`

`204 No Content`. Deletes the database record and the stored file.

## Error format

```json
{ "detail": "Human-readable message" }
```

`401` missing/invalid token · `404` not found or not owned · `413` too large · `415` unsupported type · `422` validation/processing failure.
