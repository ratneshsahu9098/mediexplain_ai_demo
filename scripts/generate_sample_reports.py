"""Generate synthetic laboratory report PDFs for development and demos.

All data is fabricated. These files contain no real patient information and
must never be presented as real clinical records.

Usage (from the repository root):
    backend\\.venv\\Scripts\\python.exe scripts\\generate_sample_reports.py
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "samples"

CBC_LINES = (
    "SYNTHETIC SAMPLE - NOT REAL PATIENT DATA",
    "MediExplain Demo Laboratory",
    "Patient Name: SAMPLE PATIENT",
    "Age / Sex: 00 / NA",
    "Sample Date: 01-Jan-2026",
    "",
    "COMPLETE BLOOD COUNT (CBC)",
    "Test Result Unit Reference Range",
    "Hemoglobin 11.2 g/dL 13.0 - 17.0",
    "WBC 7,500 /uL 4,000 - 11,000",
    "Platelets 250,000 /uL 150,000 - 450,000",
    "Hematocrit 34 % 40 - 50",
    "MCV 78 fL 80 - 100",
    "MCH 26 pg 27 - 32",
    "Neutrophils 58 % 40 - 75",
    "Lymphocytes 32 % 20 - 45",
    "",
    "This is a synthetic report generated for software testing.",
    "It must not be used for medical decisions.",
)

LIPID_LINES = (
    "SYNTHETIC SAMPLE - NOT REAL PATIENT DATA",
    "MediExplain Demo Laboratory",
    "Patient Name: SAMPLE PATIENT",
    "Sample Date: 01-Jan-2026",
    "",
    "LIPID PROFILE",
    "Test Result Unit Reference Range",
    "Total Cholesterol 220 mg/dL < 200",
    "Triglycerides 160 mg/dL < 150",
    "HDL Cholesterol 38 mg/dL > 40",
    "LDL Cholesterol 130 mg/dL < 100",
    "VLDL Cholesterol 32 mg/dL 5 - 40",
    "",
    "This is a synthetic report generated for software testing.",
    "It must not be used for medical decisions.",
)


def write_report(path: Path, title: str, lines: tuple[str, ...]) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((54, 60), title, fontsize=14, fontname="helv")
    y = 92
    for line in lines:
        if line:
            page.insert_text((54, y), line, fontsize=9.5, fontname="helv")
        y += 16
    document.save(path)
    document.close()
    print(f"wrote {path}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_report(OUTPUT_DIR / "sample_cbc_report.pdf", "CBC - Synthetic Sample", CBC_LINES)
    write_report(OUTPUT_DIR / "sample_lipid_report.pdf", "Lipid Profile - Synthetic Sample", LIPID_LINES)


if __name__ == "__main__":
    main()
