# Synthetic Sample Reports

**Every value in these files is fabricated.** They contain no real patient data and are for software development, testing and demonstration only.

| File | Contents |
|------|----------|
| `sample_cbc_report.pdf` | Complete blood count with one low hemoglobin and low MCV |
| `sample_lipid_report.pdf` | Lipid profile with high cholesterol, triglycerides and LDL |

Regenerate them with:

```powershell
backend\.venv\Scripts\python.exe scripts\generate_sample_reports.py
```

These samples are deliberately simple digital PDFs. Scanned / photographed reports are also supported through Tesseract OCR, but extraction accuracy must be measured separately.
