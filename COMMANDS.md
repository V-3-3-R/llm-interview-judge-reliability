# Commands, from a fresh machine to the final analysis

Written for Windows PowerShell in VS Code (Terminal > New Terminal, opened in this folder).
Expected outputs are given so you can tell whether each step worked. Run the steps in order.

## PHASE 0. One-time setup
```
python --version
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
- If `python` is not recognized, use `py` everywhere. If activation is blocked: `Set-ExecutionPolicy -Scope Process Bypass`, then activate again.
- In VS Code: Ctrl+Shift+P > "Python: Select Interpreter" > choose the `.venv` one.
- macOS/Linux: `source .venv/bin/activate`, and use `rm` instead of `Remove-Item`, `export KEY=value` instead of `$env:KEY="value"`.

## PHASE 1. Verify everything built so far (no API keys needed)

**1.1 Dataset check**
```
python check_manipulations.py data/answers_v0.2_reviewed.csv data/answer_key_v0.2_reviewed.csv
```
Expect: `40 questions, 320 answers checked`, `HARD FAILS: 0`, `WARNINGS: 13` (all "S6 length off", already known).

**1.2 Small dry run of the judge script (fake scores)**
```
python run_judges.py --answers data/answers_v0.2_reviewed.csv --out results_raw/scores_dry.csv --dry-run --limit 5
(Get-Content results_raw/scores_dry.csv).Count
```
Expect: `Done. 0 failures` and a count of `71` (5 answers x 2 judges x 7 conditions = 70 rows, plus the header).

**1.3 Full pipeline test on fake scores (checks that the analysis runs)**
```
python run_judges.py --answers data/answers_v0.2_reviewed.csv --out results_raw/scores_fake_full.csv --dry-run
python analyze_results.py --scores results_raw/scores_fake_full.csv --key data/answer_key_v0.2_reviewed.csv --answers data/answers_v0.2_reviewed.csv --human human_rating/human_ratings_merged_4raters.csv --out results_fake
```
Expect: line count of the fake file `4481` (320 x 2 x 7 + header); the analysis prints several tables and ends with `All tables saved in results_fake`. The first table, the human ceiling, should show 4 raters, 100 answers, mean pairwise QWK about 0.949 and minimum about 0.939. Every other number comes from random fake scores and means nothing.

**1.4 Delete all fake output so it can never mix with real data**
```
Remove-Item results_raw\scores_dry.csv, results_raw\scores_fake_full.csv
Remove-Item -Recurse results_fake
```

## PHASE 2. Decisions to make before freezing (no commands, just edits)
1. Open `run_judges.py` and confirm the model IDs at the top (`gemini-3.5-flash-lite`, `openai/gpt-oss-20b`). Write them down with today's date for the paper.
2. The judge prompt now says "computer science instructor" (it said "database instructor", which does not fit seven domains). Keep it, or change it now. After the real run starts it must never change.
3. Optional: add a stronger third judge: fill in the `gpt` entry (model ID), set `OPENAI_API_KEY`, and use `--judges gemini,groq_gptoss,gpt` below (6,720 calls instead of 4,480).
4. Read the 14 flagged answers (`review_flag` column in `data/answer_key_v0.2_reviewed.csv`) and the two Q24 edits one last time.

## PHASE 3. Freeze the dataset (run once; no edits after this)
```
python freeze_dataset.py data/answers_v0.2_reviewed.csv data/answer_key_v0.2_reviewed.csv
Get-FileHash frozen\answers_final.csv
```
Expect: `HARD FAILS: 0`, `Dataset frozen: <date>`, `Answers: 320`, and a `frozen` folder with `answers_final.csv`, `answer_key_final.csv`, `FROZEN_MANIFEST.txt`. Copy the fingerprint into your notes. A second run refuses to overwrite.

## PHASE 4. Keys and a tiny real test
Set the keys for this terminal window only (never save them in files, never paste them in chat):
```
$env:GEMINI_API_KEY="your_key_here"
$env:GROQ_API_KEY="your_key_here"
$env:GEMINI_API_KEY.Length
```
Then test three answers:
```
python run_judges.py --answers frozen/answers_final.csv --out results_raw/scores_test.csv --limit 3 --sleep 2
```
Expect: `Done. 0 failures` and 43 lines (3 x 2 x 7 + header). Open the file: scores should be integers 0 to 5 with short justifications. Then delete it:
```
Remove-Item results_raw\scores_test.csv
```

## PHASE 5. The real judge run (4,480 calls; runs for hours)
```
python run_judges.py --answers frozen/answers_final.csv --out results_raw/scores_real.csv --judges gemini,groq_gptoss --sleep 1
```
- If it stops (rate limit, network, daily quota): run the same command again. It skips finished calls and continues.
- You can run one judge at a time: use `--judges gemini`, later `--judges groq_gptoss`, both with the same `--out` file.
- Stop it with Ctrl+C at any time; nothing is lost.
- Check progress:
```
(Get-Content results_raw\scores_real.csv).Count
```
The finished file has `4481` lines. Failed calls are printed as FAILED; rerun until none remain.

## PHASE 6. Analysis on the real scores
```
python analyze_results.py --scores results_raw/scores_real.csv --key frozen/answer_key_final.csv --answers frozen/answers_final.csv --human human_rating/human_ratings_merged_4raters.csv --out results
```
Outputs in `results/`: `1_agreement.csv`, `2_consistency.csv`, `3_variant_means.csv`, `4_style_bias.csv`, `5_rubric_sensitivity.csv`, `6_cross_judge.csv`, `7_mixed_models.txt`, `variant_means.png`, `report.txt`. Send `report.txt` (and the PNG) to Claude for interpretation and for the Results and Discussion sections.

## PHASE 7. Paper
Fill the [brackets] in `docs/paper_draft_v0.1_introduction.md`, then write Sections II to VI with the results.

## If something goes wrong
| Symptom | Fix |
|---|---|
| `Set the model ID for 'gpt'` | You listed `gpt` in `--judges` without filling its model ID; remove it or fill it |
| `Set environment variable GEMINI_API_KEY` | Set the key in the same terminal window you run the script in |
| Many `FAILED ... 429` lines | Rate limit: raise `--sleep` (for example 3) and rerun the same command |
| `ModuleNotFoundError` | The virtual environment is not active, or run `pip install -r requirements.txt` again |
| `frozen/answers_final.csv already exists` | Correct behavior: the dataset is already frozen |
| Analysis says `mixed model skipped` | `pip install statsmodels` |
