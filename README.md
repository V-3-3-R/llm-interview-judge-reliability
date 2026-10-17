# LLM Interview-Grader Reliability Study: project folder

Question: how reliably do LLM judges score technical interview answers (agreement with humans, consistency across runs, style bias, rubric sensitivity)?

## Folder map

| Path | What it is |
|---|---|
| `run_judges.py` | Sends every answer to the LLM judges and saves scores (7 calls per answer per judge) |
| `check_manipulations.py` | Tests that the dataset variants really differ as intended |
| `apply_review.py` | Applies label-review edits to an answers file and logs changes (only for edits you have read) |
| `freeze_dataset.py` | Locks the final dataset with SHA-256 fingerprints (run once) |
| `analyze_results.py` | Produces all result tables and a chart from the judge scores |
| `data/archive_candidate/` | Earlier candidate answers and key (before the label review). Do not use for the real run |
| `data/label_review_S5-S8_REVIEWED_v2.csv` | Reviewed label sheet for the 160 partial/incorrect answers (verdicts, notes, flags, the 2 edits) |
| `data/answers_v0.2_reviewed.csv` | The 320 reviewed answers for the judges (random IDs, no labels) |
| `data/answer_key_v0.2_reviewed.csv` | Labels per answer (variant, quality, style, domain, `human_rated`, `review_flag`). Ready to freeze |
| `COMMANDS.md` | Every command in order with expected outputs |
| `human_rating/human_ratings_merged_4raters.csv` | Scores from the 4 raters on the 100-answer subset |
| `human_rating/raw_returned/` | The four returned rater workbooks (keep unchanged as raw data) |
| `docs/` | Protocol, paper draft (Introduction + skeleton + references), collaborator briefing PDF |

## How to run it
See **COMMANDS.md**: every command in order (setup, checks, freeze, real run, analysis) with the output you should expect.

## Rules to keep the study valid
- Do not edit answers after any judge has run.
- Do not change the judge prompt or rubrics between judges or runs.
- Human reference rules were fixed in advance: all 4 raters used; mean for correlation and error, median rounded half-up for kappa.
- Keep `human_rating/raw_returned/` untouched.
- The answers were drafted by an LLM and then reviewed; describe them as "LLM-assisted, human-verified" in the paper.
- The judge prompt in `run_judges.py` says "computer science instructor" (changed from "database instructor", which did not fit seven domains). Keep it fixed once the real run starts.

## Known limitations (also for the paper)
Short definitional questions; single-LLM authorship of answers; S6 answers longer than S1; humans score nearly all correct answers 5, so style bias on correct answers can show only as scores lower than 5; two small judges; most references are preprints.
