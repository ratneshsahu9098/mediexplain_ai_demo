# Roadmap and Task Tracker

## Phases

### Phase 1 — Basic working prototype (complete)

- [x] FastAPI project, config, database models
- [x] Register / login / JWT / bcrypt
- [x] PDF upload with validation and duplicate detection
- [x] PyMuPDF text extraction + pdfplumber tables
- [x] Tesseract OCR fallback for scans/images
- [x] Structured extraction of test / value / unit / range
- [x] Rule-based LOW / HIGH / NORMAL / UNKNOWN classification
- [x] Deterministic + LLM explanation service
- [x] Backend test suite (37 tests passing)
- [x] React frontend (landing, auth, dashboard, upload, report)
- [x] AI explanation UI with language selection

**Goal achieved:** upload a CBC PDF → extracted values → ranges → flags → explanation,
all through the web UI.

### Phase 2 — Intelligent application (current)

- [x] Hindi / Hinglish explanation output
- [x] Report-grounded chatbot endpoint + UI
- [ ] Report history filters and reopen
- [ ] Better scanned-report accuracy (deskew, crop, preprocessing)
- [ ] Frontend charts and trends

### Phase 3 — Advanced major project

- [ ] Medical knowledge base (MedlinePlus / NIH / NHS / WHO)
- [ ] Embeddings + ChromaDB retrieval
- [ ] RAG answers with source citations
- [ ] Multi-report comparison
- [ ] PDF export with disclaimer
- [ ] Local/cloud AI switching in UI

## 10-week schedule

| Week | Focus | Milestone |
|------|-------|-----------|
| 1 | Requirements, architecture, synthetic reports | Plan complete |
| 2 | Frontend setup, landing, auth, dashboard | Frontend prototype |
| 3 | FastAPI, DB, auth, upload API | Working upload backend |
| 4 | PDF extraction, OCR, tables, cleaning | Extracted report text |
| 5 | Extraction + analysis engine | Structured medical data |
| 6 | Ollama + Qwen explanations | AI explanations |
| 7 | RAG knowledge base + citations | Working chatbot |
| 8 | History, comparison, charts, export | Complete dashboard |
| 9 | Accuracy, security, authorization testing | Tested application |
| 10 | Deployment, docs, PPT, demo | Final submission |

## Checklist

### Planning
- [x] Finalise requirements
- [x] Architecture and data-flow docs
- [x] Synthetic sample reports for CBC and lipid (more categories to add)

### Backend
- [x] FastAPI scaffolding
- [x] Database models
- [x] Authentication
- [x] Report upload API

### Processing
- [x] PDF text extraction
- [x] OCR fallback
- [x] Structured test extraction
- [x] Reference-range validation

### AI
- [x] Ollama/Qwen provider + fallback
- [x] Explanation generation
- [ ] RAG knowledge base
- [x] Report chatbot (grounded, safety refusals, offline fallback)

### Advanced
- [ ] History + comparison UI
- [ ] Analytics + PDF export

### Testing
- [x] Extraction and analysis unit tests
- [x] End-to-end API flow test
- [ ] Measured accuracy on verified dataset
- [ ] Privacy and authorization review

### Submission
- [ ] Documentation and PPT
- [ ] Deployment + demo script
