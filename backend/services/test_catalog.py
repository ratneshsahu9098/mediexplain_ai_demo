"""Canonical laboratory test catalogue and alias matching.

Aliases are matched case-insensitively with flexible separators, so
"HbA1c", "Hb A1c" and "glycated hemoglobin" all resolve to one test.

The catalogue contains *names only*. It deliberately does not contain
reference ranges: ranges must always come from the specific laboratory
report, because they vary by lab, method, age, sex and other factors.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class TestInfo:
    canonical: str
    display: str
    category: str
    aliases: tuple[str, ...]


TESTS: tuple[TestInfo, ...] = (
    # --- Complete blood count ---
    TestInfo("hemoglobin", "Hemoglobin", "CBC",
             ("hemoglobin", "haemoglobin", "hgb", "hb")),
    TestInfo("rbc", "RBC Count", "CBC",
             ("red blood cell count", "total rbc", "rbc count", "rbc")),
    TestInfo("wbc", "WBC Count", "CBC",
             ("total leucocyte count", "total leukocyte count",
              "white blood cell count", "wbc count", "tlc", "wbc")),
    TestInfo("platelets", "Platelet Count", "CBC",
             ("platelet count", "platelets", "plt")),
    TestInfo("hematocrit", "Hematocrit", "CBC",
             ("hematocrit", "haematocrit", "packed cell volume", "pcv", "hct")),
    TestInfo("mcv", "MCV", "CBC",
             ("mean corpuscular volume", "mcv")),
    TestInfo("mch", "MCH", "CBC",
             ("mean corpuscular hemoglobin", "mean corpuscular haemoglobin", "mch")),
    TestInfo("mchc", "MCHC", "CBC",
             ("mean corpuscular hemoglobin concentration",
              "mean corpuscular haemoglobin concentration", "mchc")),
    TestInfo("rdw", "RDW", "CBC",
             ("rdw cv", "rdw-cv", "red cell distribution width", "rdw")),
    TestInfo("neutrophils", "Neutrophils", "CBC",
             ("neutrophils", "neutrophil", "neut")),
    TestInfo("lymphocytes", "Lymphocytes", "CBC",
             ("lymphocytes", "lymphocyte", "lymph")),
    TestInfo("monocytes", "Monocytes", "CBC",
             ("monocytes", "monocyte", "mono")),
    TestInfo("eosinophils", "Eosinophils", "CBC",
             ("eosinophils", "eosinophil", "eos")),
    TestInfo("basophils", "Basophils", "CBC",
             ("basophils", "basophil", "baso")),
    TestInfo("esr", "ESR", "CBC",
             ("erythrocyte sedimentation rate", "esr")),

    # --- Glucose ---
    TestInfo("fasting_glucose", "Fasting Blood Glucose", "Glucose",
             ("fasting blood sugar", "fasting blood glucose", "fasting glucose",
              "glucose fasting", "fbs")),
    TestInfo("random_glucose", "Random Blood Glucose", "Glucose",
             ("random blood sugar", "random blood glucose", "random glucose",
              "glucose random", "rbs")),
    TestInfo("postprandial_glucose", "Postprandial Blood Glucose", "Glucose",
             ("postprandial blood sugar", "post prandial blood sugar",
              "postprandial glucose", "ppbs")),
    TestInfo("hba1c", "HbA1c", "Glucose",
             ("glycated hemoglobin", "glycosylated hemoglobin", "hb a1c",
              "hba1c", "glycated haemoglobin")),
    TestInfo("glucose", "Blood Glucose", "Glucose",
             ("blood glucose", "blood sugar", "glucose")),

    # --- Lipid profile ---
    TestInfo("total_cholesterol", "Total Cholesterol", "Lipid",
             ("total cholesterol", "serum cholesterol", "cholesterol")),
    TestInfo("triglycerides", "Triglycerides", "Lipid",
             ("triglycerides", "triglyceride", "tg")),
    TestInfo("hdl", "HDL Cholesterol", "Lipid",
             ("hdl cholesterol", "hdl-c", "hdl")),
    TestInfo("ldl", "LDL Cholesterol", "Lipid",
             ("ldl cholesterol", "ldl-c", "ldl")),
    TestInfo("vldl", "VLDL Cholesterol", "Lipid",
             ("vldl cholesterol", "vldl")),

    # --- Liver function ---
    TestInfo("bilirubin_total", "Total Bilirubin", "Liver",
             ("total bilirubin", "bilirubin total", "bilirubin")),
    TestInfo("bilirubin_direct", "Direct Bilirubin", "Liver",
             ("direct bilirubin", "bilirubin direct", "conjugated bilirubin")),
    TestInfo("sgot", "SGOT (AST)", "Liver",
             ("aspartate aminotransferase", "sgot", "ast")),
    TestInfo("sgpt", "SGPT (ALT)", "Liver",
             ("alanine aminotransferase", "sgpt", "alt")),
    TestInfo("alp", "Alkaline Phosphatase", "Liver",
             ("alkaline phosphatase", "alp")),
    TestInfo("ggt", "GGT", "Liver",
             ("gamma glutamyl transferase", "gamma gt", "ggt")),
    TestInfo("albumin", "Albumin", "Liver",
             ("serum albumin", "albumin")),
    TestInfo("total_protein", "Total Protein", "Liver",
             ("total protein", "serum total protein")),
    TestInfo("globulin", "Globulin", "Liver",
             ("globulin",)),

    # --- Kidney function ---
    TestInfo("creatinine", "Creatinine", "Kidney",
             ("serum creatinine", "creatinine")),
    TestInfo("urea", "Blood Urea", "Kidney",
             ("blood urea", "serum urea", "urea")),
    TestInfo("bun", "Blood Urea Nitrogen", "Kidney",
             ("blood urea nitrogen", "bun")),
    TestInfo("uric_acid", "Uric Acid", "Kidney",
             ("uric acid", "serum uric acid")),
    TestInfo("egfr", "eGFR", "Kidney",
             ("estimated gfr", "egfr")),
    TestInfo("sodium", "Sodium", "Kidney",
             ("sodium", "na+")),
    TestInfo("potassium", "Potassium", "Kidney",
             ("potassium", "k+")),
    TestInfo("chloride", "Chloride", "Kidney",
             ("chloride", "cl-")),
    TestInfo("calcium", "Calcium", "Kidney",
             ("serum calcium", "calcium")),

    # --- Thyroid ---
    TestInfo("tsh", "TSH", "Thyroid",
             ("thyroid stimulating hormone", "thyrotropin", "tsh")),
    TestInfo("t3", "Total T3", "Thyroid",
             ("total t3", "t3")),
    TestInfo("t4", "Total T4", "Thyroid",
             ("total t4", "t4")),
    TestInfo("ft3", "Free T3", "Thyroid",
             ("free t3", "ft3")),
    TestInfo("ft4", "Free T4", "Thyroid",
             ("free t4", "ft4")),

    # --- Vitamins and other ---
    TestInfo("vitamin_d", "Vitamin D", "Vitamin",
             ("25-oh vitamin d", "25 oh vitamin d", "vitamin d3", "vitamin d", "vit d")),
    TestInfo("vitamin_b12", "Vitamin B12", "Vitamin",
             ("vitamin b12", "vit b12", "cyanocobalamin", "b12")),
    TestInfo("crp", "C-Reactive Protein", "Other",
             ("c-reactive protein", "c reactive protein", "crp")),
    TestInfo("iron", "Serum Iron", "Other",
             ("serum iron", "iron")),
    TestInfo("ferritin", "Ferritin", "Other",
             ("ferritin",)),
    TestInfo("hbsag", "HBsAg", "Other",
             ("hepatitis b surface antigen", "hbsag")),
    TestInfo("hiv", "HIV", "Other",
             ("hiv 1 2", "hiv")),
)

CATEGORY_LABELS = {
    "CBC": "Complete Blood Count (CBC)",
    "Glucose": "Blood Glucose",
    "Lipid": "Lipid Profile",
    "Liver": "Liver Function Test",
    "Kidney": "Kidney Function Test",
    "Thyroid": "Thyroid Profile",
    "Vitamin": "Vitamin Profile",
    "Other": "General",
}

_CATEGORY_PRIORITY = ("CBC", "Lipid", "Liver", "Kidney", "Thyroid", "Glucose", "Vitamin", "Other")


def _alias_pattern(alias: str) -> re.Pattern[str]:
    parts = [re.escape(p) for p in re.split(r"[\s\-_/]+", alias.strip()) if p]
    body = r"[\s\-_/]*".join(parts)
    return re.compile(
        rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


@lru_cache
def _catalogue() -> tuple[tuple[re.Pattern[str], TestInfo], ...]:
    entries: list[tuple[re.Pattern[str], TestInfo]] = []
    for info in TESTS:
        for alias in info.aliases:
            entries.append((_alias_pattern(alias), info))
    # Longest alias first, so "total cholesterol" beats "cholesterol".
    entries.sort(key=lambda item: len(item[0].pattern), reverse=True)
    return tuple(entries)


@dataclass(frozen=True)
class TestMatch:
    info: TestInfo
    start: int
    end: int
    text: str


def match_test(line: str) -> TestMatch | None:
    if not line:
        return None
    for pattern, info in _catalogue():
        match = pattern.search(line)
        if match:
            return TestMatch(info=info, start=match.start(), end=match.end(), text=match.group(0))
    return None


def detect_report_type(canonicals: set[str]) -> str:
    """Pick the dominant report category from the tests that were found."""
    if not canonicals:
        return "Unknown"

    by_canonical = {info.canonical: info.category for info in TESTS}
    counts: dict[str, int] = {}
    for canonical in canonicals:
        category = by_canonical.get(canonical)
        if category:
            counts[category] = counts.get(category, 0) + 1

    if not counts:
        return "General"

    def rank(item: tuple[str, int]) -> tuple[int, int]:
        category, count = item
        return count, -_CATEGORY_PRIORITY.index(category)

    best_category, best_count = max(counts.items(), key=rank)
    if best_count >= 2 or best_category in {"Glucose", "Other"}:
        return CATEGORY_LABELS.get(best_category, "General")
    return "General"
