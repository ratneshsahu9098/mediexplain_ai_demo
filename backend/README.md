# MediExplain AI — Backend

FastAPI backend for report upload, document processing, structured extraction, rule-based analysis, and AI explanations.

## Requirements

- Python **3.10+**
- Tesseract OCR (optional, needed for scanned reports)
  - Windows: install from <https://github.com/UB-Mannheim/tesseract/wiki>
  - Set `TESSERACT_CMD` in `.env` if it is not on `PATH`
- Ollama + a Qwen model (optional, needed for LLM explanations)

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/health>

The SQLite database (`backend/mediexplain.db`) and the `data/` directories are created automatically on first start.

## Configuration

All settings come from environment variables / `.env` (see `../.env.example`).

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev value | JWT signing key — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime |
| `DATABASE_URL` | `sqlite:///./mediexplain.db` | SQLAlchemy URL |
| `UPLOAD_DIR` | `../data/uploads` | Private upload storage |
| `MAX_UPLOAD_MB` | `15` | Max upload size |
| `MAX_PDF_PAGES` | `25` | Max pages processed |
| `TESSERACT_CMD` | auto | Path to `tesseract.exe` |
| `AI_PROVIDER` | `ollama` | `ollama`, `openrouter`, `cloud` or `none` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local model |
| `OPENROUTER_API_KEY` | empty | OpenRouter key; required when `AI_PROVIDER=openrouter` |
| `OPENROUTER_MODEL` | `openrouter/auto` | Any OpenRouter model slug |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter-compatible base URL |
| `OPENROUTER_SITE_URL` | empty | Optional attribution header |
| `CLOUD_LLM_API_KEY` | empty | Other hosted provider key (optional) |
| `CLOUD_LLM_MODEL` | empty | Other hosted model name |

## Processing pipeline

```text
services/document_processor.py   orchestration + persisted artifacts
├── pdf_extractor.py             PyMuPDF text, page images, pdfplumber tables
├── ocr_engine.py                Tesseract fallback with availability detection
├── table_extractor.py           pdfplumber table rows → normalized lines
├── data_normalizer.py           text cleanup, unit + number normalization
├── test_parser.py               line parser → structured test results
├── medical_analyzer.py          range comparison, unit conversion, flags
├── explanation_service.py       LLM explanations + deterministic fallback
└── ai/
    ├── llm_provider.py          provider interface + factory
    ├── ollama_provider.py       local Ollama client
    ├── openrouter_provider.py   OpenRouter client
    ├── cloud_provider.py        OpenAI-compatible cloud client
    └── prompts.py               safety-constrained prompt templates
```

### Extraction strategy

1. Open the PDF with PyMuPDF. If a page contains selectable text, use it.
2. Enrich with `pdfplumber` table rows (fixed-width tabular reports).
3. For image-only pages (or JPG/PNG uploads), render at ~300 DPI and run Tesseract.
4. Normalize whitespace, unicode units, thousands separators, decimal commas.
5. Parse each line into `{name, value, unit, range, flag, confidence}`.
6. Never invent a reference range. If the report does not show one, the result is `UNKNOWN`.

### Analysis rules

| Condition | Status |
|-----------|--------|
| Value below report's lower bound | `LOW` |
| Value inside report's interval | `NORMAL` |
| Value above report's upper bound | `HIGH` |
| No reference range in report | `UNKNOWN` |
| No numeric value (qualitative result) | `NOT_APPLICABLE` / `NEEDS_REVIEW` |
| Unparseable numeric value | `NEEDS_REVIEW` |

Unit conversion is applied only when the value unit and reference-range unit differ and a known conversion exists; the conversion is recorded on the result. Critical-value flags are configurable in `services/critical_values.py` and are **placeholder thresholds requiring clinical validation**.

## API

| Method | Endpoint | Notes |
|--------|----------|-------|
| `GET` | `/api/health` | Public |
| `POST` | `/api/auth/register` | JSON `{name, email, password}` |
| `POST` | `/api/auth/login` | JSON `{email, password}` → JWT |
| `GET` | `/api/auth/me` | Bearer token |
| `POST` | `/api/reports/upload` | `multipart/form-data` field `file` |
| `GET` | `/api/reports` | List own reports |
| `GET` | `/api/reports/{id}` | Own report + results |
| `GET` | `/api/reports/{id}/results` | Own results |
| `POST` | `/api/reports/{id}/analyze` | Re-run analysis |
| `POST` | `/api/reports/{id}/explain` | Generate explanations (`?language=en`) |
| `DELETE` | `/api/reports/{id}` | Delete report + file |

### Example: register, upload and explain

```powershell
$email = "demo@example.com"
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/register `
  -ContentType 'application/json' `
  -Body (@{ name = 'Demo User'; email = $email; password = 'demo12345' } | ConvertTo-Json)

$token = (Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/login `
  -ContentType 'application/json' `
  -Body (@{ email = $email; password = 'demo12345' } | ConvertTo-Json)).access_token

# curl.exe is used because Windows PowerShell 5.1 has no -Form parameter.
$upload = curl.exe -s -X POST http://localhost:8000/api/reports/upload `
  -H "Authorization: Bearer $token" `
  -F "file=@..\samples\sample_cbc_report.pdf;type=application/pdf" | ConvertFrom-Json

curl.exe -s -X POST "http://localhost:8000/api/reports/$($upload.id)/explain?language=en" `
  -H "Authorization: Bearer $token"
```

A `.env` with `AI_PROVIDER=ollama` but no running Ollama returns template
explanations (`provider: "template"`) instead of failing.

### Using OpenRouter

1. Create a key at <https://openrouter.ai/keys>.
2. Set these values in `backend/.env`:

   ```dotenv
   AI_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENROUTER_MODEL=openrouter/auto
   ```

3. Restart the API. `GET /api/health` should report `"ai_provider": "openrouter:openrouter/auto"`.

Any OpenRouter model slug works, for example
`openrouter/auto`, `meta-llama/llama-3.1-8b-instruct`, or a `:free` variant such
as `nvidia/nemotron-3-ultra-550b-a55b:free`.
Free variants are rate-limited by OpenRouter. The key stays server-side and is
never exposed to the frontend; if a request fails, explanations fall back to
templates and the response is marked `source: "template"`.

### Demo data

From the repository root:

```powershell
backend\.venv\Scripts\python.exe scripts\seed_demo.py
```

This creates `demo@mediexplain.app` / `DemoPass123` with both synthetic sample
reports attached. Re-running the script resets the demo password and skips
duplicate uploads. Never use these credentials in a public deployment.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

The suite covers:

- Number/unit/range parsing (`tests/test_parser.py`)
- LOW/HIGH/NORMAL/UNKNOWN classification and unit conversion (`tests/test_analyzer.py`)
- Auth + upload → analyze → explain flow with an in-memory DB and a synthetic PDF (`tests/test_api_flow.py`)

AI calls are mocked/disabled in tests, so no Ollama instance is required.

## Adding a new laboratory test

1. Add aliases and the canonical name to `services/test_catalog.py`.
2. Add a unit conversion pair to `services/units.py` if needed.
3. Add critical thresholds (only with clinical review) to `services/critical_values.py`.
4. Add parser/analyzer test cases.

## Safety notes

- Uploaded files are stored under `UPLOAD_DIR`, never inside a static web directory.
- The LLM never changes extracted values; it receives them read-only as context.
- Explanations are explicitly labelled as AI-generated, unverified educational content.
