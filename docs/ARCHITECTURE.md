# Architecture

## 1. Layers

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Frontend | React + Vite | UI, upload, dashboards, chat |
| API | FastAPI | Auth, validation, authorization, orchestration |
| Processing | PyMuPDF, pdfplumber, Tesseract | Text, tables, OCR |
| Analysis | Python (deterministic) | Value/range comparison, flags |
| AI | Ollama + Qwen / hosted LLM | Explanations, chat |
| Storage | SQLite/PostgreSQL + ChromaDB | Metadata, reports, knowledge |

## 2. Upload → analysis flow

```mermaid
sequenceDiagram
    actor U as User
    participant F as React client
    participant A as FastAPI
    participant P as Document processor
    participant E as Extraction/Analysis
    participant D as Database
    participant L as LLM provider

    U->>F: Select PDF/JPG/PNG
    F->>A: POST /api/reports/upload (JWT)
    A->>A: Validate extension, signature, size
    A->>A: Hash file (duplicate check per user)
    A->>D: Create report (status=processing)
    A->>P: Process file
    P->>P: Text? PyMuPDF + pdfplumber : OCR
    P->>E: Normalized lines
    E->>E: Parse + classify each result
    E->>D: Persist test results
    A->>D: status=completed
    A->>F: Report + results
    U->>F: Request explanations
    F->>A: POST /api/reports/{id}/explain
    A->>L: Safety-constrained prompt (report context)
    L->>A: Explanation text
    A->>D: Persist explanations
    A->>F: Explanations + disclaimer
```

## 3. AI provider abstraction

```text
ExplanationService / ChatService
            │
            ▼
       LLMProvider (ABC)
       ├── OllamaProvider  → POST /api/generate
       └── CloudProvider   → OpenAI-compatible /chat/completions
```

Selection is configuration-only (`AI_PROVIDER`). If the configured provider fails, the service returns deterministic template explanations and marks the response `source: "template"` — the app never fabricates a value.

## 4. Database schema (MVP)

```mermaid
erDiagram
    USERS ||--o{ REPORTS : owns
    REPORTS ||--o{ TEST_RESULTS : contains
    TEST_RESULTS ||--o{ EXPLANATIONS : has

    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        datetime created_at
    }
    REPORTS {
        int id PK
        int user_id FK
        string original_filename
        string stored_path
        string mime_type
        int file_size
        string file_hash
        string report_type
        string status
        string extraction_method
        int page_count
        string error_message
        datetime created_at
    }
    TEST_RESULTS {
        int id PK
        int report_id FK
        string test_name
        string raw_name
        float value
        string value_text
        string unit
        float range_low
        float range_high
        string range_text
        string range_unit
        string status
        bool unit_converted
        bool critical_flag
        float confidence
        int source_page
        string notes
    }
    EXPLANATIONS {
        int id PK
        int result_id FK
        string language
        string text
        string model
        string source
        datetime created_at
    }
    CHAT_MESSAGES {
        int id PK
        int report_id FK
        int user_id FK
        string role
        string content
        string language
        string model
        string source
        json cited_result_ids
        datetime created_at
    }
```

Design decisions:

- Original file is stored separately from extracted results.
- The laboratory's units and ranges are preserved; no global default range is applied.
- Extraction confidence and validation status are stored per result.
- `source_page` supports traceability to the original document.
- LLM output is stored in `explanations`, never overwriting `test_results`.
- Chat transcripts are stored per report; the assistant may only use that report's
  extracted results, and diagnosis/prescription requests are refused before the
  model is called.
- Every report query is scoped by `user_id`.

## 5. Error handling

| Failure | Behaviour |
|---------|-----------|
| Corrupt/unreadable PDF | Report `status=failed`, message stored, HTTP 422 |
| Tesseract not installed | Text extraction still works; scanned uploads fail with a clear message |
| Ollama offline | Template explanations/chat, `source=template`, HTTP 200 |
| Duplicate file (same user) | HTTP 409 with existing report id |
| Unauthorized report access | HTTP 404 (does not leak existence) |

## 6. Deployment

Development: React dev server + uvicorn + SQLite + local Ollama.

Production-style: static frontend host, containerised API, PostgreSQL, private object storage, hosted or dedicated-GPU inference. Never expose a development Ollama endpoint publicly.
