#!/usr/bin/env python3
"""Apply your edits from the review sheet to the answers file.
Usage: python apply_review.py answers_in.csv label_review_S5-S8.csv answers_out.csv
Only rows with text in 'replacement_text' are changed. Every change is logged to change_log.csv.
Remember: if you change S5, change its partner S7 (same omission); S6 and S8 likewise."""
import csv, sys, datetime
inp, rev, out = sys.argv[1:4]
rows = list(csv.DictReader(open(inp, encoding="utf-8")))
repl = {r["answer_id"]: r["replacement_text"].strip() for r in csv.DictReader(open(rev, encoding="utf-8-sig")) if r["replacement_text"].strip()}
log = []
for r in rows:
    new = repl.get(r["answer_id"])
    if new and new != r["answer"]:
        log.append({"answer_id": r["answer_id"], "old": r["answer"], "new": new, "when": datetime.datetime.now().isoformat(timespec="seconds")})
        r["answer"] = new
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
if log:
    new_file = False
    try: open("change_log.csv").close()
    except FileNotFoundError: new_file = True
    with open("change_log.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["answer_id","old","new","when"])
        if new_file: w.writeheader()
        w.writerows(log)
print(f"{len(log)} answers changed; log in change_log.csv. Now re-run check_manipulations.py on {out}")
