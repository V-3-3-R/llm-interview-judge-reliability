# Reliability of LLM Judges for Technical Interview Answers

**Agreement · Consistency · Style Bias · Rubric Sensitivity**

This repository contains the full dataset, code, analysis scripts, and results for the study:

> *Reliability of LLM Judges for Technical Interview Answers: Agreement, Consistency, and Style Bias*

**Author:** Veer Javadia  
**Email:** veerjavadia@gmail.com  
**GitHub:** [V-3-3-R](https://github.com/V-3-3-R)

---

## Research Question

How reliably do LLM judges score technical interview answers?

We measure:
- Agreement with human raters
- Consistency across repeated runs
- Style bias (when technical content is held constant)
- Sensitivity to rubric wording

---

## Key Facts

| Item | Value |
|------|-------|
| Questions | 40 (7 computing domains) |
| Answers | 320 (8 controlled variants each) |
| Human raters | 4 independent raters on 100 answers |
| Judges | Gemini 3.5 Flash-Lite + gpt-oss-20b |
| Total judge calls | 4,480 |
| Freezing date | 10 October 2026 (IST) |

---

## Folder Map

| Path | Description |
|------|-------------|
| `run_judges.py` | Sends every answer to the LLM judges (7 calls per answer per judge) |
| `check_manipulations.py` | Verifies that the answer variants differ as intended |
| `apply_review.py` | Applies label-review edits and logs changes |
| `freeze_dataset.py` | Locks the final dataset with SHA-256 fingerprints |
| `analyze_results.py` | Produces all main result tables |
| `extra_analysis.py` | Sensitivity and exploratory analyses |
| `progress.py` | Tracks how many judge scores are complete |
| `data/answers_v0.2_reviewed.csv` | 320 reviewed answers (no labels) |
| `data/answer_key_v0.2_reviewed.csv` | Labels (variant, quality, style, domain, flags) |
| `data/label_review_S5-S8_REVIEWED_v2.csv` | Full review of the 160 partial/incorrect answers |
| `frozen/` | Final frozen answers + key (do not edit) |
| `human_rating/human_ratings_merged_4raters.csv` | Merged scores from 4 raters |
| `human_rating/raw_returned/` | Original returned workbooks (keep unchanged) |
| `results/` | Main analysis outputs |
| `results_extra/` | Sensitivity / exploratory outputs |
| `results_raw/` | Raw judge scores (4,480 rows) |
| `docs/` | Protocol, paper drafts, briefing |
| `COMMANDS.md` | Every command in order with expected outputs |

---

## How to Reproduce

See **`COMMANDS.md`** for the complete sequence (setup → checks → freeze → real run → analysis).

Quick start:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python analyze_results.py
